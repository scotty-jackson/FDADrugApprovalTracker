"""
API router for clinical trials.
Provides endpoints for searching and viewing trials from ClinicalTrials.gov and other registries.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func
from typing import List, Optional
from datetime import date
import logging
import math

from app.database import get_db
from app import schemas, models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trials", tags=["trials"])


@router.get("", response_model=dict)
def list_trials(
    search: Optional[str] = Query(None),
    phase: Optional[models.TrialPhase] = Query(None),
    status: Optional[models.TrialStatus] = Query(None),
    disease_area: Optional[str] = Query(None),
    ticker: Optional[str] = Query(None),
    registry: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List clinical trials with comprehensive filtering.

    Supports filtering by phase, status, disease area, company ticker, date ranges, and more.
    """
    try:
        query = db.query(models.Trial).options(
            joinedload(models.Trial.sponsor),
            joinedload(models.Trial.conditions),
            joinedload(models.Trial.interventions)
        )

        # Search in title, registry_id, or intervention names
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    models.Trial.title.ilike(search_term),
                    models.Trial.registry_id.ilike(search_term)
                )
            )

        # Filter by phase
        if phase:
            query = query.filter(models.Trial.phase == phase)

        # Filter by status
        if status:
            query = query.filter(models.Trial.status == status)

        # Filter by disease area
        if disease_area:
            query = query.join(models.TrialCondition).filter(
                models.TrialCondition.disease_area == disease_area
            )

        # Filter by ticker
        if ticker:
            query = query.join(models.Sponsor).join(models.CompanyMapping).filter(
                models.CompanyMapping.ticker.ilike(f"%{ticker}%")
            )

        # Filter by registry
        if registry:
            query = query.filter(models.Trial.registry == registry)

        # Date range filters
        if date_from:
            query = query.filter(models.Trial.primary_completion_date >= date_from)
        if date_to:
            query = query.filter(models.Trial.primary_completion_date <= date_to)

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        trials = query.order_by(models.Trial.last_update_date.desc()).offset(offset).limit(page_size).all()
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "items": [schemas.Trial.model_validate(trial) for trial in trials]
        }

    except Exception as e:
        logger.error(f"Error listing trials: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{trial_id}", response_model=schemas.TrialDetail)
def get_trial(trial_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific trial.
    """
    try:
        trial = db.query(models.Trial).options(
            joinedload(models.Trial.sponsor),
            joinedload(models.Trial.conditions),
            joinedload(models.Trial.interventions),
            joinedload(models.Trial.outcomes),
            joinedload(models.Trial.results)
        ).filter(models.Trial.id == trial_id).first()

        if not trial:
            raise HTTPException(status_code=404, detail="Trial not found")

        return schemas.TrialDetail.model_validate(trial)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trial {trial_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/registry/{registry_id}", response_model=schemas.TrialDetail)
def get_trial_by_registry_id(registry_id: str, db: Session = Depends(get_db)):
    """
    Get trial by registry ID (e.g., NCT number).
    """
    try:
        trial = db.query(models.Trial).options(
            joinedload(models.Trial.sponsor),
            joinedload(models.Trial.conditions),
            joinedload(models.Trial.interventions),
            joinedload(models.Trial.outcomes),
            joinedload(models.Trial.results)
        ).filter(models.Trial.registry_id == registry_id).first()

        if not trial:
            raise HTTPException(status_code=404, detail=f"Trial {registry_id} not found")

        return schemas.TrialDetail.model_validate(trial)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trial {registry_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats/by-phase", response_model=dict)
def get_trials_by_phase(db: Session = Depends(get_db)):
    """
    Get trial counts grouped by phase.
    """
    try:
        results = db.query(
            models.Trial.phase,
            func.count(models.Trial.id).label('count')
        ).filter(
            models.Trial.phase.isnot(None)
        ).group_by(models.Trial.phase).all()

        return {
            "by_phase": [
                {"phase": str(row.phase.value), "count": row.count}
                for row in results
            ]
        }

    except Exception as e:
        logger.error(f"Error getting trial stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
