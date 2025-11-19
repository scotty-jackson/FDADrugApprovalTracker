"""
API router for FDA event-related endpoints (PDUFA dates, advisory committees, etc.).
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
import logging
import math

from app.database import get_db
from app import schemas, services
from app.models import EventType, EventStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=dict)
def list_events(
    event_type: Optional[EventType] = Query(None, description="Filter by event type (PDUFA, ADCOM, etc.)"),
    event_status: Optional[EventStatus] = Query(None, description="Filter by event status"),
    date_from: Optional[date] = Query(None, description="Filter events from this date"),
    date_to: Optional[date] = Query(None, description="Filter events until this date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of FDA-related events with filtering.

    Events include:
    - PDUFA dates (Prescription Drug User Fee Act target action dates)
    - Advisory Committee meetings
    - Filing acceptances
    - Decision announcements

    Returns:
        - total: Total number of events matching filters
        - page: Current page number
        - page_size: Number of items per page
        - total_pages: Total number of pages
        - items: List of events with drug information
    """
    try:
        filters = schemas.EventFilters(
            event_type=event_type,
            event_status=event_status,
            date_from=date_from,
            date_to=date_to,
            page=page,
            page_size=page_size
        )

        events, total = services.get_events(db, filters)
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "items": [schemas.EventWithDrug.model_validate(event) for event in events]
        }
    except Exception as e:
        logger.error(f"Error listing events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/upcoming", response_model=dict)
def list_upcoming_events(
    days: int = Query(90, ge=1, le=365, description="Number of days to look ahead"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get upcoming events within the specified number of days.
    Only returns scheduled events that haven't occurred yet.
    """
    try:
        from datetime import datetime, timedelta

        today = datetime.utcnow().date()
        future_date = today + timedelta(days=days)

        filters = schemas.EventFilters(
            event_status=EventStatus.SCHEDULED,
            date_from=today,
            date_to=future_date,
            page=page,
            page_size=page_size
        )

        events, total = services.get_events(db, filters)
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "items": [schemas.EventWithDrug.model_validate(event) for event in events]
        }
    except Exception as e:
        logger.error(f"Error listing upcoming events: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
