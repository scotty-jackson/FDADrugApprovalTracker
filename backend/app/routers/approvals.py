"""
API router for approval-related endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import logging
import math

from app.database import get_db
from app import schemas, services
from app.models import FDACenter, ApplicationType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("", response_model=dict)
def list_approvals(
    search: Optional[str] = Query(None, description="Search in drug name or application number"),
    fda_center: Optional[FDACenter] = Query(None, description="Filter by FDA center (CDER/CBER)"),
    application_type: Optional[ApplicationType] = Query(None, description="Filter by application type"),
    therapeutic_area: Optional[str] = Query(None, description="Filter by therapeutic area"),
    sponsor_name: Optional[str] = Query(None, description="Filter by sponsor name"),
    ticker: Optional[str] = Query(None, description="Filter by company ticker symbol"),
    date_from: Optional[date] = Query(None, description="Filter approvals from this date"),
    date_to: Optional[date] = Query(None, description="Filter approvals until this date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of FDA approvals with comprehensive filtering.

    Supports filtering by:
    - Search term (matches drug name or application number)
    - FDA center (CDER or CBER)
    - Application type (NDA, BLA, sNDA, etc.)
    - Therapeutic area
    - Sponsor/company name
    - Stock ticker symbol
    - Date range

    Returns:
        - total: Total number of approvals matching filters
        - page: Current page number
        - page_size: Number of items per page
        - total_pages: Total number of pages
        - items: List of approvals with drug information
    """
    try:
        filters = schemas.ApprovalFilters(
            search=search,
            fda_center=fda_center,
            application_type=application_type,
            therapeutic_area=therapeutic_area,
            sponsor_name=sponsor_name,
            ticker=ticker,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size
        )

        approvals, total = services.get_approvals(db, filters)
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "items": [schemas.ApprovalWithDrug.model_validate(approval) for approval in approvals]
        }
    except Exception as e:
        logger.error(f"Error listing approvals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{approval_id}", response_model=schemas.ApprovalWithDrug)
def get_approval(
    approval_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific approval.
    """
    try:
        from app.models import Approval
        from sqlalchemy.orm import joinedload

        approval = db.query(Approval).options(
            joinedload(Approval.drug).joinedload(Drug.sponsor)
        ).filter(Approval.id == approval_id).first()

        if not approval:
            raise HTTPException(status_code=404, detail="Approval not found")

        return schemas.ApprovalWithDrug.model_validate(approval)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting approval {approval_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
