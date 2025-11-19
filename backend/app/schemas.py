"""
Pydantic schemas for API request and response validation.
These schemas define the structure of data sent to and from the API.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from app.models import FDACenter, ApplicationType, DecisionOutcome, EventType, EventStatus


# Sponsor Schemas
class SponsorBase(BaseModel):
    name: str
    notes: Optional[str] = None


class SponsorCreate(SponsorBase):
    pass


class Sponsor(SponsorBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Company Mapping Schemas
class CompanyMappingBase(BaseModel):
    company_name: str
    ticker: Optional[str] = None
    exchange: Optional[str] = None
    notes: Optional[str] = None


class CompanyMappingCreate(CompanyMappingBase):
    sponsor_id: int


class CompanyMapping(CompanyMappingBase):
    id: int
    sponsor_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Drug Schemas
class DrugBase(BaseModel):
    drug_name: str
    brand_name: Optional[str] = None
    generic_name: Optional[str] = None
    primary_indication: Optional[str] = None
    therapeutic_area: Optional[str] = None
    route_of_administration: Optional[str] = None


class DrugCreate(DrugBase):
    sponsor_id: Optional[int] = None


class Drug(DrugBase):
    id: int
    sponsor_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DrugDetail(Drug):
    """Extended drug information including related data."""
    sponsor: Optional[Sponsor] = None
    approvals: List['Approval'] = []
    events: List['Event'] = []

    model_config = ConfigDict(from_attributes=True)


# Approval Schemas
class ApprovalBase(BaseModel):
    fda_center: Optional[FDACenter] = None
    approval_date: Optional[date] = None
    application_type: Optional[ApplicationType] = None
    application_number: Optional[str] = None
    decision_outcome: DecisionOutcome = DecisionOutcome.APPROVED
    indication: Optional[str] = None
    label_url: Optional[str] = None
    press_release_url: Optional[str] = None
    fda_page_url: Optional[str] = None
    notes: Optional[str] = None


class ApprovalCreate(ApprovalBase):
    drug_id: int


class Approval(ApprovalBase):
    id: int
    drug_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApprovalWithDrug(Approval):
    """Approval information with associated drug details."""
    drug: Optional[Drug] = None

    model_config = ConfigDict(from_attributes=True)


# Event Schemas
class EventBase(BaseModel):
    event_type: EventType
    event_date: Optional[date] = None
    event_status: EventStatus = EventStatus.SCHEDULED
    application_number: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    source_url: Optional[str] = None


class EventCreate(EventBase):
    drug_id: Optional[int] = None


class Event(EventBase):
    id: int
    drug_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventWithDrug(Event):
    """Event information with associated drug details."""
    drug: Optional[Drug] = None

    model_config = ConfigDict(from_attributes=True)


# Pagination Schema
class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[dict]  # Will be specific type depending on endpoint


# Summary/Statistics Schemas
class ApprovalsByMonth(BaseModel):
    """Aggregated approval counts by month."""
    month: str  # Format: YYYY-MM
    count: int


class ApprovalsByTherapeuticArea(BaseModel):
    """Aggregated approval counts by therapeutic area."""
    therapeutic_area: str
    count: int


class ApprovalsByCenter(BaseModel):
    """Aggregated approval counts by FDA center."""
    fda_center: str
    count: int


class ApprovalsByType(BaseModel):
    """Aggregated approval counts by application type."""
    application_type: str
    count: int


class SummaryStats(BaseModel):
    """High-level summary statistics for the dashboard."""
    total_drugs: int
    total_approvals: int
    total_upcoming_events: int
    recent_approvals_30d: int
    approvals_by_month: List[ApprovalsByMonth]
    approvals_by_therapeutic_area: List[ApprovalsByTherapeuticArea]
    approvals_by_center: List[ApprovalsByCenter]
    approvals_by_type: List[ApprovalsByType]


# Search and Filter Schemas
class DrugFilters(BaseModel):
    """Query parameters for filtering drugs."""
    search: Optional[str] = None
    therapeutic_area: Optional[str] = None
    sponsor_id: Optional[int] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ApprovalFilters(BaseModel):
    """Query parameters for filtering approvals."""
    search: Optional[str] = None
    fda_center: Optional[FDACenter] = None
    application_type: Optional[ApplicationType] = None
    therapeutic_area: Optional[str] = None
    sponsor_name: Optional[str] = None
    ticker: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class EventFilters(BaseModel):
    """Query parameters for filtering events."""
    event_type: Optional[EventType] = None
    event_status: Optional[EventStatus] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
