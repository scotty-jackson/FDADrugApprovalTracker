"""
Pydantic schemas for API request and response validation.
These schemas define the structure of data sent to and from the API.
"""
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, List
from datetime import date, datetime
from app.models import FDACenter, ApplicationType, DecisionOutcome, EventType, EventStatus, NotificationType


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


# Subscription Schemas
class SubscriberCreate(BaseModel):
    """Schema for creating a new subscriber."""
    email: EmailStr


class SubscriberUpdate(BaseModel):
    """Schema for updating subscriber preferences."""
    notify_new_approvals: Optional[bool] = None
    notify_new_events: Optional[bool] = None
    notify_event_reminders: Optional[bool] = None
    notify_event_updates: Optional[bool] = None
    reminder_days_before: Optional[int] = Field(None, ge=1, le=30)
    digest_mode: Optional[bool] = None


class Subscriber(BaseModel):
    """Subscriber information."""
    id: int
    email: str
    is_active: bool
    is_verified: bool
    notify_new_approvals: bool
    notify_new_events: bool
    notify_event_reminders: bool
    notify_event_updates: bool
    reminder_days_before: int
    digest_mode: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DrugSubscriptionCreate(BaseModel):
    """Schema for subscribing to a drug."""
    drug_id: int


class DrugSubscriptionResponse(BaseModel):
    """Response for drug subscription."""
    id: int
    drug_id: int
    drug_name: str
    created_at: datetime


class SubscriptionStatusResponse(BaseModel):
    """Response indicating subscription status."""
    subscribed: bool
    message: str
    subscriber: Optional[Subscriber] = None


class VerifyEmailResponse(BaseModel):
    """Response for email verification."""
    success: bool
    message: str


# ============================================================================
# CLINICAL TRIALS SCHEMAS
# ============================================================================

from app.models import (
    TrialPhase, TrialStatus, StudyType, InterventionType,
    OutcomeType, CatalystType, CatalystProbability
)


# Trial Schemas
class TrialBase(BaseModel):
    registry: str
    registry_id: str
    title: str
    status: Optional[TrialStatus] = None
    phase: Optional[TrialPhase] = None
    study_type: Optional[StudyType] = None
    start_date: Optional[date] = None
    primary_completion_date: Optional[date] = None
    completion_date: Optional[date] = None
    location_summary: Optional[str] = None
    brief_summary: Optional[str] = None


class TrialCreate(TrialBase):
    sponsor_id: Optional[int] = None


class Trial(TrialBase):
    id: int
    sponsor_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TrialCondition(BaseModel):
    id: int
    condition_name: str
    disease_area: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TrialIntervention(BaseModel):
    id: int
    intervention_type: Optional[InterventionType] = None
    intervention_name: str
    description: Optional[str] = None
    linked_drug_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class TrialOutcome(BaseModel):
    id: int
    outcome_type: OutcomeType
    measure: str
    time_frame: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TrialResult(BaseModel):
    id: int
    results_available: bool
    results_url: Optional[str] = None
    primary_outcome_summary: Optional[str] = None
    reported_success_flag: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class TrialDetail(Trial):
    """Extended trial with all related data."""
    sponsor: Optional[Sponsor] = None
    conditions: List[TrialCondition] = []
    interventions: List[TrialIntervention] = []
    outcomes: List[TrialOutcome] = []
    results: Optional[TrialResult] = None

    model_config = ConfigDict(from_attributes=True)


# Catalyst Schemas
class CatalystBase(BaseModel):
    catalyst_type: CatalystType
    expected_date: Optional[date] = None
    probability_band: CatalystProbability = CatalystProbability.MEDIUM
    title: str
    description: Optional[str] = None
    disease_area: Optional[str] = None


class CatalystCreate(CatalystBase):
    trial_id: Optional[int] = None
    drug_id: Optional[int] = None
    company_mapping_id: Optional[int] = None


class Catalyst(CatalystBase):
    id: int
    trial_id: Optional[int] = None
    drug_id: Optional[int] = None
    company_mapping_id: Optional[int] = None
    is_auto_generated: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CatalystWithDetails(Catalyst):
    """Catalyst with related trial/drug/company info."""
    trial: Optional[Trial] = None
    drug: Optional[Drug] = None
    company: Optional[CompanyMapping] = None

    model_config = ConfigDict(from_attributes=True)


# Company Dashboard Schemas
class CompanyStats(BaseModel):
    """Aggregated statistics for a company."""
    company_id: int
    company_name: str
    ticker: Optional[str] = None
    total_trials: int
    trials_by_phase: dict
    total_drugs: int
    total_approvals: int
    active_disease_areas: List[str]
    upcoming_catalysts_count: int


class CompanyDetail(BaseModel):
    """Detailed company information."""
    company: CompanyMapping
    sponsors: List[Sponsor]
    trials: List[TrialDetail]
    drugs: List[DrugDetail]
    approvals: List[ApprovalWithDrug]
    catalysts: List[CatalystWithDetails]
    stats: CompanyStats


# Disease Area Schemas  
class DiseaseAreaStats(BaseModel):
    """Statistics for a disease area."""
    disease_area: str
    total_trials: int
    trials_by_phase: dict
    trials_by_status: dict
    total_drugs: int
    total_companies: int
    top_companies: List[dict]  # [{name, ticker, trial_count}]
    recent_approvals_count: int


# Trial Filters
class TrialFilters(BaseModel):
    search: Optional[str] = None
    phase: Optional[TrialPhase] = None
    status: Optional[TrialStatus] = None
    disease_area: Optional[str] = None
    sponsor_id: Optional[int] = None
    ticker: Optional[str] = None
    registry: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# Catalyst Filters
class CatalystFilters(BaseModel):
    catalyst_type: Optional[CatalystType] = None
    disease_area: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    ticker: Optional[str] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
