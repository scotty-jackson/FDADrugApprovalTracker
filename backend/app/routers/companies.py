"""
API router for company pipeline dashboards.
Provides company-level views of trials, drugs, approvals, and catalysts.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, distinct
from typing import List
import logging

from app.database import get_db
from app import schemas, models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=List[schemas.CompanyMapping])
def list_companies(
    search: Optional[str] = Query(None),
    has_ticker: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List all companies with optional filtering.
    """
    try:
        query = db.query(models.CompanyMapping).options(
            joinedload(models.CompanyMapping.sponsor)
        )

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    models.CompanyMapping.company_name.ilike(search_term),
                    models.CompanyMapping.ticker.ilike(search_term)
                )
            )

        if has_ticker is not None:
            if has_ticker:
                query = query.filter(models.CompanyMapping.ticker.isnot(None))
            else:
                query = query.filter(models.CompanyMapping.ticker.is_(None))

        companies = query.order_by(models.CompanyMapping.company_name).all()

        return [schemas.CompanyMapping.model_validate(c) for c in companies]

    except Exception as e:
        logger.error(f"Error listing companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_id}/stats", response_model=dict)
def get_company_stats(company_id: int, db: Session = Depends(get_db)):
    """
    Get aggregated statistics for a company.
    """
    try:
        company = db.query(models.CompanyMapping).filter(
            models.CompanyMapping.id == company_id
        ).first()

        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Get sponsor IDs for this company
        sponsor_id = company.sponsor_id

        # Count trials
        total_trials = db.query(models.Trial).filter(
            models.Trial.sponsor_id == sponsor_id
        ).count()

        # Trials by phase
        trials_by_phase_raw = db.query(
            models.Trial.phase,
            func.count(models.Trial.id).label('count')
        ).filter(
            models.Trial.sponsor_id == sponsor_id,
            models.Trial.phase.isnot(None)
        ).group_by(models.Trial.phase).all()

        trials_by_phase = {
            str(row.phase.value): row.count
            for row in trials_by_phase_raw
        }

        # Count drugs
        total_drugs = db.query(models.Drug).filter(
            models.Drug.sponsor_id == sponsor_id
        ).count()

        # Count approvals
        total_approvals = db.query(models.Approval).join(models.Drug).filter(
            models.Drug.sponsor_id == sponsor_id
        ).count()

        # Active disease areas
        disease_areas = db.query(
            distinct(models.TrialCondition.disease_area)
        ).join(models.Trial).filter(
            models.Trial.sponsor_id == sponsor_id,
            models.TrialCondition.disease_area.isnot(None)
        ).all()

        active_disease_areas = [area[0] for area in disease_areas if area[0]]

        # Upcoming catalysts
        upcoming_catalysts_count = db.query(models.Catalyst).filter(
            models.Catalyst.company_mapping_id == company_id,
            models.Catalyst.expected_date >= func.current_date()
        ).count()

        return {
            "company_id": company_id,
            "company_name": company.company_name,
            "ticker": company.ticker,
            "total_trials": total_trials,
            "trials_by_phase": trials_by_phase,
            "total_drugs": total_drugs,
            "total_approvals": total_approvals,
            "active_disease_areas": active_disease_areas[:10],  # Top 10
            "upcoming_catalysts_count": upcoming_catalysts_count
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_id}/trials", response_model=List[schemas.Trial])
def get_company_trials(
    company_id: int,
    phase: Optional[models.TrialPhase] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get all trials for a company, optionally filtered by phase.
    """
    try:
        company = db.query(models.CompanyMapping).filter(
            models.CompanyMapping.id == company_id
        ).first()

        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        query = db.query(models.Trial).filter(
            models.Trial.sponsor_id == company.sponsor_id
        )

        if phase:
            query = query.filter(models.Trial.phase == phase)

        trials = query.order_by(models.Trial.primary_completion_date).all()

        return [schemas.Trial.model_validate(t) for t in trials]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting company trials: {e}")
        raise HTTPException(status_code=500, detail=str(e))
