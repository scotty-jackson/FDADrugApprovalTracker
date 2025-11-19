"""
Business logic layer for FDA Drug Approval Tracker.
Contains service functions for querying and manipulating data.
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, extract, or_, and_, desc
from typing import List, Tuple, Optional
from datetime import datetime, timedelta
import logging

from app import models, schemas

logger = logging.getLogger(__name__)


# Drug Services
def get_drugs(
    db: Session,
    filters: schemas.DrugFilters
) -> Tuple[List[models.Drug], int]:
    """
    Get paginated list of drugs with optional filtering.
    Returns (drugs, total_count).
    """
    query = db.query(models.Drug).options(joinedload(models.Drug.sponsor))

    # Apply search filter
    if filters.search:
        search_term = f"%{filters.search}%"
        query = query.filter(
            or_(
                models.Drug.drug_name.ilike(search_term),
                models.Drug.brand_name.ilike(search_term),
                models.Drug.generic_name.ilike(search_term)
            )
        )

    # Apply therapeutic area filter
    if filters.therapeutic_area:
        query = query.filter(models.Drug.therapeutic_area == filters.therapeutic_area)

    # Apply sponsor filter
    if filters.sponsor_id:
        query = query.filter(models.Drug.sponsor_id == filters.sponsor_id)

    # Get total count before pagination
    total = query.count()

    # Apply pagination
    offset = (filters.page - 1) * filters.page_size
    drugs = query.order_by(desc(models.Drug.updated_at)).offset(offset).limit(filters.page_size).all()

    return drugs, total


def get_drug_by_id(db: Session, drug_id: int) -> Optional[models.Drug]:
    """Get a single drug by ID with all related data."""
    return db.query(models.Drug).options(
        joinedload(models.Drug.sponsor),
        joinedload(models.Drug.approvals),
        joinedload(models.Drug.events)
    ).filter(models.Drug.id == drug_id).first()


def create_drug(db: Session, drug: schemas.DrugCreate) -> models.Drug:
    """Create a new drug record."""
    db_drug = models.Drug(**drug.model_dump())
    db.add(db_drug)
    db.commit()
    db.refresh(db_drug)
    return db_drug


# Approval Services
def get_approvals(
    db: Session,
    filters: schemas.ApprovalFilters
) -> Tuple[List[models.Approval], int]:
    """
    Get paginated list of approvals with optional filtering.
    Returns (approvals, total_count).
    """
    query = db.query(models.Approval).options(
        joinedload(models.Approval.drug).joinedload(models.Drug.sponsor)
    )

    # Apply search filter (search in drug name)
    if filters.search:
        search_term = f"%{filters.search}%"
        query = query.join(models.Drug).filter(
            or_(
                models.Drug.drug_name.ilike(search_term),
                models.Drug.brand_name.ilike(search_term),
                models.Approval.application_number.ilike(search_term)
            )
        )

    # Apply FDA center filter
    if filters.fda_center:
        query = query.filter(models.Approval.fda_center == filters.fda_center)

    # Apply application type filter
    if filters.application_type:
        query = query.filter(models.Approval.application_type == filters.application_type)

    # Apply therapeutic area filter
    if filters.therapeutic_area:
        if not filters.search:  # Only join if not already joined
            query = query.join(models.Drug)
        query = query.filter(models.Drug.therapeutic_area == filters.therapeutic_area)

    # Apply sponsor name filter
    if filters.sponsor_name:
        query = query.join(models.Drug).join(models.Sponsor).filter(
            models.Sponsor.name.ilike(f"%{filters.sponsor_name}%")
        )

    # Apply ticker filter (search in company mappings)
    if filters.ticker:
        query = query.join(models.Drug).join(models.Sponsor).join(models.CompanyMapping).filter(
            models.CompanyMapping.ticker.ilike(f"%{filters.ticker}%")
        )

    # Apply date range filters
    if filters.date_from:
        query = query.filter(models.Approval.approval_date >= filters.date_from)
    if filters.date_to:
        query = query.filter(models.Approval.approval_date <= filters.date_to)

    # Get total count before pagination
    total = query.count()

    # Apply pagination and ordering
    offset = (filters.page - 1) * filters.page_size
    approvals = query.order_by(desc(models.Approval.approval_date)).offset(offset).limit(filters.page_size).all()

    return approvals, total


def create_approval(db: Session, approval: schemas.ApprovalCreate) -> models.Approval:
    """Create a new approval record."""
    db_approval = models.Approval(**approval.model_dump())
    db.add(db_approval)
    db.commit()
    db.refresh(db_approval)
    return db_approval


# Event Services
def get_events(
    db: Session,
    filters: schemas.EventFilters
) -> Tuple[List[models.Event], int]:
    """
    Get paginated list of events with optional filtering.
    Returns (events, total_count).
    """
    query = db.query(models.Event).options(
        joinedload(models.Event.drug).joinedload(models.Drug.sponsor)
    )

    # Apply event type filter
    if filters.event_type:
        query = query.filter(models.Event.event_type == filters.event_type)

    # Apply event status filter
    if filters.event_status:
        query = query.filter(models.Event.event_status == filters.event_status)

    # Apply date range filters
    if filters.date_from:
        query = query.filter(models.Event.event_date >= filters.date_from)
    if filters.date_to:
        query = query.filter(models.Event.event_date <= filters.date_to)

    # Get total count before pagination
    total = query.count()

    # Apply pagination and ordering
    offset = (filters.page - 1) * filters.page_size
    events = query.order_by(models.Event.event_date).offset(offset).limit(filters.page_size).all()

    return events, total


def create_event(db: Session, event: schemas.EventCreate) -> models.Event:
    """Create a new event record."""
    db_event = models.Event(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


# Sponsor Services
def get_or_create_sponsor(db: Session, sponsor_name: str) -> models.Sponsor:
    """Get existing sponsor or create a new one."""
    sponsor = db.query(models.Sponsor).filter(models.Sponsor.name == sponsor_name).first()
    if not sponsor:
        sponsor = models.Sponsor(name=sponsor_name)
        db.add(sponsor)
        db.commit()
        db.refresh(sponsor)
    return sponsor


def get_sponsor_by_name(db: Session, sponsor_name: str) -> Optional[models.Sponsor]:
    """Get sponsor by name."""
    return db.query(models.Sponsor).filter(models.Sponsor.name == sponsor_name).first()


def get_all_sponsors(db: Session) -> List[models.Sponsor]:
    """Get all sponsors."""
    return db.query(models.Sponsor).order_by(models.Sponsor.name).all()


# Summary/Statistics Services
def get_summary_stats(db: Session) -> schemas.SummaryStats:
    """
    Get high-level summary statistics for the dashboard.
    """
    # Total counts
    total_drugs = db.query(func.count(models.Drug.id)).scalar()
    total_approvals = db.query(func.count(models.Approval.id)).scalar()

    # Upcoming events (scheduled events in the future)
    total_upcoming_events = db.query(func.count(models.Event.id)).filter(
        models.Event.event_status == models.EventStatus.SCHEDULED,
        models.Event.event_date >= datetime.utcnow().date()
    ).scalar()

    # Recent approvals in last 30 days
    thirty_days_ago = datetime.utcnow().date() - timedelta(days=30)
    recent_approvals_30d = db.query(func.count(models.Approval.id)).filter(
        models.Approval.approval_date >= thirty_days_ago
    ).scalar()

    # Approvals by month (last 12 months)
    one_year_ago = datetime.utcnow().date() - timedelta(days=365)
    approvals_by_month_raw = db.query(
        func.to_char(models.Approval.approval_date, 'YYYY-MM').label('month'),
        func.count(models.Approval.id).label('count')
    ).filter(
        models.Approval.approval_date >= one_year_ago
    ).group_by('month').order_by('month').all()

    approvals_by_month = [
        schemas.ApprovalsByMonth(month=row.month, count=row.count)
        for row in approvals_by_month_raw
    ]

    # Approvals by therapeutic area
    approvals_by_area_raw = db.query(
        models.Drug.therapeutic_area,
        func.count(models.Approval.id).label('count')
    ).join(models.Approval).filter(
        models.Drug.therapeutic_area.isnot(None)
    ).group_by(models.Drug.therapeutic_area).order_by(desc('count')).limit(10).all()

    approvals_by_therapeutic_area = [
        schemas.ApprovalsByTherapeuticArea(
            therapeutic_area=row.therapeutic_area or 'Unknown',
            count=row.count
        )
        for row in approvals_by_area_raw
    ]

    # Approvals by FDA center
    approvals_by_center_raw = db.query(
        models.Approval.fda_center,
        func.count(models.Approval.id).label('count')
    ).filter(
        models.Approval.fda_center.isnot(None)
    ).group_by(models.Approval.fda_center).all()

    approvals_by_center = [
        schemas.ApprovalsByCenter(fda_center=str(row.fda_center.value), count=row.count)
        for row in approvals_by_center_raw
    ]

    # Approvals by application type
    approvals_by_type_raw = db.query(
        models.Approval.application_type,
        func.count(models.Approval.id).label('count')
    ).filter(
        models.Approval.application_type.isnot(None)
    ).group_by(models.Approval.application_type).all()

    approvals_by_type = [
        schemas.ApprovalsByType(application_type=str(row.application_type.value), count=row.count)
        for row in approvals_by_type_raw
    ]

    return schemas.SummaryStats(
        total_drugs=total_drugs or 0,
        total_approvals=total_approvals or 0,
        total_upcoming_events=total_upcoming_events or 0,
        recent_approvals_30d=recent_approvals_30d or 0,
        approvals_by_month=approvals_by_month,
        approvals_by_therapeutic_area=approvals_by_therapeutic_area,
        approvals_by_center=approvals_by_center,
        approvals_by_type=approvals_by_type
    )


def get_therapeutic_areas(db: Session) -> List[str]:
    """Get list of unique therapeutic areas."""
    areas = db.query(models.Drug.therapeutic_area).distinct().filter(
        models.Drug.therapeutic_area.isnot(None)
    ).all()
    return sorted([area[0] for area in areas if area[0]])
