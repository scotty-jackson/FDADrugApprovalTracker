"""
API router for drug-related endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.database import get_db
from app import schemas, services
import math

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/drugs", tags=["drugs"])


@router.get("", response_model=dict)
def list_drugs(
    search: Optional[str] = Query(None, description="Search in drug name, brand name, or generic name"),
    therapeutic_area: Optional[str] = Query(None, description="Filter by therapeutic area"),
    sponsor_id: Optional[int] = Query(None, description="Filter by sponsor ID"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of drugs with optional filtering.

    Returns:
        - total: Total number of drugs matching filters
        - page: Current page number
        - page_size: Number of items per page
        - total_pages: Total number of pages
        - items: List of drugs
    """
    try:
        filters = schemas.DrugFilters(
            search=search,
            therapeutic_area=therapeutic_area,
            sponsor_id=sponsor_id,
            page=page,
            page_size=page_size
        )

        drugs, total = services.get_drugs(db, filters)
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "items": [schemas.Drug.model_validate(drug) for drug in drugs]
        }
    except Exception as e:
        logger.error(f"Error listing drugs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{drug_id}", response_model=schemas.DrugDetail)
def get_drug(
    drug_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific drug including approvals and events.
    """
    try:
        drug = services.get_drug_by_id(db, drug_id)
        if not drug:
            raise HTTPException(status_code=404, detail="Drug not found")
        return schemas.DrugDetail.model_validate(drug)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting drug {drug_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/therapeutic-areas/list", response_model=List[str])
def list_therapeutic_areas(db: Session = Depends(get_db)):
    """
    Get list of all unique therapeutic areas.
    Useful for populating filter dropdowns.
    """
    try:
        return services.get_therapeutic_areas(db)
    except Exception as e:
        logger.error(f"Error listing therapeutic areas: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
