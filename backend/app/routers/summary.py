"""
API router for summary statistics and dashboard data.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import logging

from app.database import get_db
from app import schemas, services

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/summary", tags=["summary"])


@router.get("", response_model=schemas.SummaryStats)
def get_summary_statistics(db: Session = Depends(get_db)):
    """
    Get high-level summary statistics for the dashboard.

    Returns:
    - Total counts of drugs, approvals, and upcoming events
    - Recent approvals in the last 30 days
    - Approvals broken down by:
        - Month (last 12 months)
        - Therapeutic area (top 10)
        - FDA center (CDER vs CBER)
        - Application type (NDA, BLA, etc.)

    This endpoint is optimized for displaying dashboard charts and summary cards.
    """
    try:
        return services.get_summary_stats(db)
    except Exception as e:
        logger.error(f"Error getting summary statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sponsors", response_model=List[schemas.Sponsor])
def list_sponsors(db: Session = Depends(get_db)):
    """
    Get list of all sponsors/companies.
    Useful for populating filter dropdowns.
    """
    try:
        sponsors = services.get_all_sponsors(db)
        return [schemas.Sponsor.model_validate(sponsor) for sponsor in sponsors]
    except Exception as e:
        logger.error(f"Error listing sponsors: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
