"""
API router for investment catalysts.
Catalysts are key upcoming events like PDUFA dates, trial completions, readouts, etc.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import List, Optional
from datetime import date, datetime, timedelta
import logging
import math

from app.database import get_db
from app import schemas, models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/catalysts", tags=["catalysts"])


@router.get("", response_model=dict)
def list_catalysts(
    catalyst_type: Optional[models.CatalystType] = Query(None),
    disease_area: Optional[str] = Query(None),
    ticker: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List upcoming catalysts with filtering.
    """
    try:
        query = db.query(models.Catalyst).options(
            joinedload(models.Catalyst.trial),
            joinedload(models.Catalyst.drug),
            joinedload(models.Catalyst.company)
        )

        # Only future catalysts by default
        if not date_from:
            date_from = datetime.now().date()

        query = query.filter(models.Catalyst.expected_date >= date_from)

        # Filter by type
        if catalyst_type:
            query = query.filter(models.Catalyst.catalyst_type == catalyst_type)

        # Filter by disease area
        if disease_area:
            query = query.filter(models.Catalyst.disease_area == disease_area)

        # Filter by ticker
        if ticker:
            query = query.join(models.CompanyMapping).filter(
                models.CompanyMapping.ticker.ilike(f"%{ticker}%")
            )

        # Date range
        if date_to:
            query = query.filter(models.Catalyst.expected_date <= date_to)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        catalysts = query.order_by(models.Catalyst.expected_date).offset(offset).limit(page_size).all()
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "items": [schemas.CatalystWithDetails.model_validate(c) for c in catalysts]
        }

    except Exception as e:
        logger.error(f"Error listing catalysts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upcoming", response_model=dict)
def get_upcoming_catalysts(
    months: int = Query(6, ge=1, le=24, description="Number of months to look ahead"),
    db: Session = Depends(get_db)
):
    """
    Get catalysts grouped by month for the next N months.
    """
    try:
        today = datetime.now().date()
        end_date = today + timedelta(days=30 * months)

        catalysts = db.query(models.Catalyst).options(
            joinedload(models.Catalyst.trial),
            joinedload(models.Catalyst.drug),
            joinedload(models.Catalyst.company)
        ).filter(
            and_(
                models.Catalyst.expected_date >= today,
                models.Catalyst.expected_date <= end_date
            )
        ).order_by(models.Catalyst.expected_date).all()

        # Group by month
        by_month = {}
        for catalyst in catalysts:
            if catalyst.expected_date:
                month_key = catalyst.expected_date.strftime('%Y-%m')
                if month_key not in by_month:
                    by_month[month_key] = []
                by_month[month_key].append(schemas.CatalystWithDetails.model_validate(catalyst))

        return {
            "total": len(catalysts),
            "months": months,
            "by_month": by_month
        }

    except Exception as e:
        logger.error(f"Error getting upcoming catalysts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=dict)
def get_catalyst_stats(db: Session = Depends(get_db)):
    """
    Get catalyst statistics for the dashboard.
    """
    try:
        today = datetime.now().date()

        # Catalysts in next 3, 6, 12 months
        three_months = today + timedelta(days=90)
        six_months = today + timedelta(days=180)
        twelve_months = today + timedelta(days=365)

        count_3m = db.query(models.Catalyst).filter(
            and_(
                models.Catalyst.expected_date >= today,
                models.Catalyst.expected_date <= three_months
            )
        ).count()

        count_6m = db.query(models.Catalyst).filter(
            and_(
                models.Catalyst.expected_date >= today,
                models.Catalyst.expected_date <= six_months
            )
        ).count()

        count_12m = db.query(models.Catalyst).filter(
            and_(
                models.Catalyst.expected_date >= today,
                models.Catalyst.expected_date <= twelve_months
            )
        ).count()

        return {
            "next_3_months": count_3m,
            "next_6_months": count_6m,
            "next_12_months": count_12m
        }

    except Exception as e:
        logger.error(f"Error getting catalyst stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
