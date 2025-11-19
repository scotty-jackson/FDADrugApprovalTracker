"""
API router for disease area dashboards.
Provides disease-area-level views of trials, companies, and activity.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import List
import logging

from app.database import get_db
from app import schemas, models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/disease-areas", tags=["disease-areas"])


@router.get("", response_model=List[str])
def list_disease_areas(db: Session = Depends(get_db)):
    """
    List all unique disease areas.
    """
    try:
        # Get from trial conditions
        areas_from_trials = db.query(
            distinct(models.TrialCondition.disease_area)
        ).filter(
            models.TrialCondition.disease_area.isnot(None)
        ).all()

        # Get from drugs
        areas_from_drugs = db.query(
            distinct(models.Drug.therapeutic_area)
        ).filter(
            models.Drug.therapeutic_area.isnot(None)
        ).all()

        # Combine and deduplicate
        all_areas = set()
        for area in areas_from_trials:
            if area[0]:
                all_areas.add(area[0])
        for area in areas_from_drugs:
            if area[0]:
                all_areas.add(area[0])

        return sorted(list(all_areas))

    except Exception as e:
        logger.error(f"Error listing disease areas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{disease_area}/stats", response_model=dict)
def get_disease_area_stats(disease_area: str, db: Session = Depends(get_db)):
    """
    Get comprehensive statistics for a disease area.
    """
    try:
        # Total trials
        total_trials = db.query(models.Trial).join(models.TrialCondition).filter(
            models.TrialCondition.disease_area == disease_area
        ).count()

        # Trials by phase
        trials_by_phase_raw = db.query(
            models.Trial.phase,
            func.count(distinct(models.Trial.id)).label('count')
        ).join(models.TrialCondition).filter(
            models.TrialCondition.disease_area == disease_area,
            models.Trial.phase.isnot(None)
        ).group_by(models.Trial.phase).all()

        trials_by_phase = {
            str(row.phase.value): row.count
            for row in trials_by_phase_raw
        }

        # Trials by status
        trials_by_status_raw = db.query(
            models.Trial.status,
            func.count(distinct(models.Trial.id)).label('count')
        ).join(models.TrialCondition).filter(
            models.TrialCondition.disease_area == disease_area,
            models.Trial.status.isnot(None)
        ).group_by(models.Trial.status).all()

        trials_by_status = {
            str(row.status.value): row.count
            for row in trials_by_status_raw
        }

        # Unique drugs
        total_drugs = db.query(func.count(distinct(models.TrialIntervention.linked_drug_id))).join(
            models.Trial
        ).join(models.TrialCondition).filter(
            models.TrialCondition.disease_area == disease_area,
            models.TrialIntervention.linked_drug_id.isnot(None)
        ).scalar()

        # Unique companies/sponsors
        total_sponsors = db.query(func.count(distinct(models.Trial.sponsor_id))).join(
            models.TrialCondition
        ).filter(
            models.TrialCondition.disease_area == disease_area,
            models.Trial.sponsor_id.isnot(None)
        ).scalar()

        # Top companies by trial count
        top_companies_raw = db.query(
            models.CompanyMapping.company_name,
            models.CompanyMapping.ticker,
            func.count(distinct(models.Trial.id)).label('trial_count')
        ).join(
            models.Sponsor, models.CompanyMapping.sponsor_id == models.Sponsor.id
        ).join(
            models.Trial, models.Trial.sponsor_id == models.Sponsor.id
        ).join(
            models.TrialCondition
        ).filter(
            models.TrialCondition.disease_area == disease_area
        ).group_by(
            models.CompanyMapping.company_name,
            models.CompanyMapping.ticker
        ).order_by(
            func.count(distinct(models.Trial.id)).desc()
        ).limit(10).all()

        top_companies = [
            {
                "name": row.company_name,
                "ticker": row.ticker,
                "trial_count": row.trial_count
            }
            for row in top_companies_raw
        ]

        # Recent approvals in this area
        from datetime import datetime, timedelta
        six_months_ago = datetime.now().date() - timedelta(days=180)

        recent_approvals = db.query(func.count(models.Approval.id)).join(
            models.Drug
        ).filter(
            models.Drug.therapeutic_area == disease_area,
            models.Approval.approval_date >= six_months_ago
        ).scalar()

        return {
            "disease_area": disease_area,
            "total_trials": total_trials,
            "trials_by_phase": trials_by_phase,
            "trials_by_status": trials_by_status,
            "total_drugs": total_drugs or 0,
            "total_companies": total_sponsors or 0,
            "top_companies": top_companies,
            "recent_approvals_count": recent_approvals or 0
        }

    except Exception as e:
        logger.error(f"Error getting disease area stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
