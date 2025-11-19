"""
SQLAlchemy database models for FDA Drug Approval Tracker.
Defines the schema for drugs, approvals, sponsors, company mappings, and events.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()


class FDACenter(str, enum.Enum):
    """FDA regulatory centers."""
    CDER = "CDER"  # Center for Drug Evaluation and Research
    CBER = "CBER"  # Center for Biologics Evaluation and Research
    UNKNOWN = "UNKNOWN"


class ApplicationType(str, enum.Enum):
    """FDA application types."""
    NDA = "NDA"  # New Drug Application
    BLA = "BLA"  # Biologics License Application
    ANDA = "ANDA"  # Abbreviated New Drug Application
    SNDA = "sNDA"  # Supplemental New Drug Application
    SBLA = "sBLA"  # Supplemental Biologics License Application
    OTHER = "OTHER"


class DecisionOutcome(str, enum.Enum):
    """FDA decision outcomes."""
    APPROVED = "APPROVED"
    TENTATIVE_APPROVAL = "TENTATIVE_APPROVAL"
    COMPLETE_RESPONSE = "COMPLETE_RESPONSE"  # CRL - rejection
    PENDING = "PENDING"
    WITHDRAWN = "WITHDRAWN"


class EventType(str, enum.Enum):
    """Types of FDA-related events."""
    PDUFA = "PDUFA"  # Prescription Drug User Fee Act date
    ADCOM = "ADCOM"  # Advisory Committee meeting
    FILING_ACCEPTANCE = "FILING_ACCEPTANCE"
    DECISION = "DECISION"
    OTHER = "OTHER"


class EventStatus(str, enum.Enum):
    """Status of upcoming events."""
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    DELAYED = "DELAYED"
    CANCELLED = "CANCELLED"


class Sponsor(Base):
    """
    Pharmaceutical sponsors/companies that submit FDA applications and trials.
    """
    __tablename__ = "sponsors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    sponsor_type = Column(String(50), nullable=True)  # pharma, biotech, academic, other
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    drugs = relationship("Drug", back_populates="sponsor")
    company_mappings = relationship("CompanyMapping", back_populates="sponsor")


class CompanyMapping(Base):
    """
    Maps sponsor names to publicly traded companies and their tickers.
    Allows for flexible expansion as more mapping data becomes available.
    Supports many-to-many: multiple sponsors can map to one company.
    """
    __tablename__ = "company_mappings"

    id = Column(Integer, primary_key=True, index=True)
    sponsor_id = Column(Integer, ForeignKey("sponsors.id"), nullable=False)
    company_name = Column(String(255), nullable=False, index=True)
    ticker = Column(String(20), nullable=True, index=True)
    exchange = Column(String(20), nullable=True)  # e.g., NASDAQ, NYSE
    confidence_score = Column(Integer, nullable=True)  # 0-100, confidence in mapping accuracy
    mapping_source = Column(String(50), default="manual")  # manual, heuristic, api, etc.
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    sponsor = relationship("Sponsor", back_populates="company_mappings")


class Drug(Base):
    """
    Drugs that have been submitted for FDA approval or approved.
    Contains general drug information.
    """
    __tablename__ = "drugs"

    id = Column(Integer, primary_key=True, index=True)
    drug_name = Column(String(500), nullable=False, index=True)  # Generic or common name
    brand_name = Column(String(500), nullable=True, index=True)
    generic_name = Column(String(500), nullable=True)
    primary_indication = Column(Text, nullable=True)
    therapeutic_area = Column(String(255), nullable=True, index=True)
    route_of_administration = Column(String(100), nullable=True)
    sponsor_id = Column(Integer, ForeignKey("sponsors.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sponsor = relationship("Sponsor", back_populates="drugs")
    approvals = relationship("Approval", back_populates="drug")
    events = relationship("Event", back_populates="drug")


class Approval(Base):
    """
    FDA approval records for drugs.
    Tracks approval history including initial approvals and supplements.
    """
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    drug_id = Column(Integer, ForeignKey("drugs.id"), nullable=False)
    fda_center = Column(SQLEnum(FDACenter), nullable=True, index=True)
    approval_date = Column(Date, nullable=True, index=True)
    application_type = Column(SQLEnum(ApplicationType), nullable=True, index=True)
    application_number = Column(String(50), nullable=True, unique=True, index=True)
    decision_outcome = Column(SQLEnum(DecisionOutcome), default=DecisionOutcome.APPROVED)
    indication = Column(Text, nullable=True)  # Specific indication for this approval
    label_url = Column(String(1000), nullable=True)
    press_release_url = Column(String(1000), nullable=True)
    fda_page_url = Column(String(1000), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    drug = relationship("Drug", back_populates="approvals")


class Event(Base):
    """
    Upcoming FDA-related events such as PDUFA dates and advisory committees.
    """
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    drug_id = Column(Integer, ForeignKey("drugs.id"), nullable=True)
    event_type = Column(SQLEnum(EventType), nullable=False, index=True)
    event_date = Column(Date, nullable=True, index=True)
    event_status = Column(SQLEnum(EventStatus), default=EventStatus.SCHEDULED, index=True)
    application_number = Column(String(50), nullable=True, index=True)
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    source_url = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    drug = relationship("Drug", back_populates="events")


class NotificationType(str, enum.Enum):
    """Types of notifications users can receive."""
    NEW_APPROVAL = "NEW_APPROVAL"  # New approval for a drug
    NEW_EVENT = "NEW_EVENT"  # New PDUFA or event added
    EVENT_REMINDER = "EVENT_REMINDER"  # Upcoming event reminder
    EVENT_UPDATE = "EVENT_UPDATE"  # Event status changed
    APPROVAL_UPDATE = "APPROVAL_UPDATE"  # Approval info updated


class Subscriber(Base):
    """
    Email subscribers who want to receive notifications about drugs.
    Passwordless system - users manage subscriptions via email links.
    """
    __tablename__ = "subscribers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)  # Can unsubscribe
    verification_token = Column(String(100), unique=True, nullable=True)  # For email verification
    is_verified = Column(Boolean, default=False, index=True)

    # Notification preferences
    notify_new_approvals = Column(Boolean, default=True)
    notify_new_events = Column(Boolean, default=True)
    notify_event_reminders = Column(Boolean, default=True)  # X days before event
    notify_event_updates = Column(Boolean, default=True)
    reminder_days_before = Column(Integer, default=7)  # Days before event to send reminder

    # Frequency preferences
    digest_mode = Column(Boolean, default=False)  # Send daily digest vs instant notifications

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_notification_at = Column(DateTime, nullable=True)

    # Relationships
    subscriptions = relationship("DrugSubscription", back_populates="subscriber", cascade="all, delete-orphan")
    notifications = relationship("NotificationLog", back_populates="subscriber")


class DrugSubscription(Base):
    """
    Links subscribers to specific drugs they want to track.
    """
    __tablename__ = "drug_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    subscriber_id = Column(Integer, ForeignKey("subscribers.id"), nullable=False, index=True)
    drug_id = Column(Integer, ForeignKey("drugs.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    subscriber = relationship("Subscriber", back_populates="subscriptions")
    drug = relationship("Drug")

    # Ensure unique subscriber-drug combinations
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class NotificationLog(Base):
    """
    Tracks notifications sent to subscribers.
    Prevents duplicate notifications and provides audit trail.
    """
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    subscriber_id = Column(Integer, ForeignKey("subscribers.id"), nullable=False, index=True)
    drug_id = Column(Integer, ForeignKey("drugs.id"), nullable=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True, index=True)
    approval_id = Column(Integer, ForeignKey("approvals.id"), nullable=True, index=True)
    notification_type = Column(SQLEnum(NotificationType), nullable=False, index=True)

    subject = Column(String(500), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow, index=True)
    email_sent_successfully = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    subscriber = relationship("Subscriber", back_populates="notifications")
    drug = relationship("Drug")
    event = relationship("Event")
    approval = relationship("Approval")

# ============================================================================
# CLINICAL TRIALS MODELS
# ============================================================================

class TrialPhase(str, enum.Enum):
    """Clinical trial phases."""
    EARLY_PHASE_1 = "Early Phase 1"
    PHASE_1 = "Phase 1"
    PHASE_1_PHASE_2 = "Phase 1/Phase 2"
    PHASE_2 = "Phase 2"
    PHASE_2_PHASE_3 = "Phase 2/Phase 3"
    PHASE_3 = "Phase 3"
    PHASE_4 = "Phase 4"
    NOT_APPLICABLE = "Not Applicable"


class TrialStatus(str, enum.Enum):
    """Overall trial status."""
    RECRUITING = "Recruiting"
    NOT_YET_RECRUITING = "Not yet recruiting"
    ENROLLING_BY_INVITATION = "Enrolling by invitation"
    ACTIVE_NOT_RECRUITING = "Active, not recruiting"
    COMPLETED = "Completed"
    SUSPENDED = "Suspended"
    TERMINATED = "Terminated"
    WITHDRAWN = "Withdrawn"
    UNKNOWN = "Unknown status"


class StudyType(str, enum.Enum):
    """Type of clinical study."""
    INTERVENTIONAL = "Interventional"
    OBSERVATIONAL = "Observational"
    EXPANDED_ACCESS = "Expanded Access"


class InterventionType(str, enum.Enum):
    """Type of intervention in a trial."""
    DRUG = "Drug"
    BIOLOGICAL = "Biological"
    DEVICE = "Device"
    PROCEDURE = "Procedure"
    BEHAVIORAL = "Behavioral"
    DIETARY_SUPPLEMENT = "Dietary Supplement"
    OTHER = "Other"


class OutcomeType(str, enum.Enum):
    """Type of trial outcome measure."""
    PRIMARY = "Primary"
    SECONDARY = "Secondary"
    OTHER = "Other"


class CatalystType(str, enum.Enum):
    """Types of catalysts/events investors track."""
    PRIMARY_COMPLETION = "Primary Completion"
    STUDY_COMPLETION = "Study Completion"
    TOPLINE_READOUT = "Top-line Readout"
    FDA_DECISION = "FDA Decision"
    PDUFA_DATE = "PDUFA Date"
    ADCOM_MEETING = "AdCom Meeting"
    CONFERENCE_PRESENTATION = "Conference Presentation"
    LABEL_EXPANSION = "Label Expansion"
    REGULATORY_FILING = "Regulatory Filing"
    OTHER = "Other"


class CatalystProbability(str, enum.Enum):
    """Confidence level for catalyst timing."""
    HIGH = "High"  # Confirmed date
    MEDIUM = "Medium"  # Expected based on timelines
    LOW = "Low"  # Speculative


class Trial(Base):
    """
    Clinical trials from ClinicalTrials.gov, EUCTR, and other registries.
    """
    __tablename__ = "trials"

    id = Column(Integer, primary_key=True, index=True)
    registry = Column(String(50), nullable=False, index=True)  # e.g., "ClinicalTrials.gov", "EUCTR"
    registry_id = Column(String(100), nullable=False, unique=True, index=True)  # NCT number or EUCTR ID
    title = Column(Text, nullable=False)
    status = Column(SQLEnum(TrialStatus), nullable=True, index=True)
    phase = Column(SQLEnum(TrialPhase), nullable=True, index=True)
    study_type = Column(SQLEnum(StudyType), nullable=True)
    
    # Dates
    start_date = Column(Date, nullable=True, index=True)
    primary_completion_date = Column(Date, nullable=True, index=True)
    completion_date = Column(Date, nullable=True, index=True)
    last_update_date = Column(Date, nullable=True, index=True)
    
    # Sponsor and location
    sponsor_id = Column(Integer, ForeignKey("sponsors.id"), nullable=True, index=True)
    location_summary = Column(String(255), nullable=True)  # e.g., "United States", "Global", "EU"
    
    # Study design
    allocation = Column(String(50), nullable=True)
    masking = Column(String(100), nullable=True)
    intervention_model = Column(String(100), nullable=True)
    primary_purpose = Column(String(100), nullable=True)
    
    # URLs and identifiers
    registry_url = Column(String(1000), nullable=True)
    brief_summary = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sponsor = relationship("Sponsor")
    conditions = relationship("TrialCondition", back_populates="trial", cascade="all, delete-orphan")
    interventions = relationship("TrialIntervention", back_populates="trial", cascade="all, delete-orphan")
    outcomes = relationship("TrialOutcome", back_populates="trial", cascade="all, delete-orphan")
    results = relationship("TrialResult", back_populates="trial", uselist=False, cascade="all, delete-orphan")


class TrialCondition(Base):
    """
    Conditions/diseases being studied in a trial.
    """
    __tablename__ = "trial_conditions"

    id = Column(Integer, primary_key=True, index=True)
    trial_id = Column(Integer, ForeignKey("trials.id"), nullable=False, index=True)
    condition_name = Column(String(500), nullable=False, index=True)
    disease_area = Column(String(255), nullable=True, index=True)  # Normalized category: Oncology, NASH, etc.
    
    # Relationships
    trial = relationship("Trial", back_populates="conditions")


class TrialIntervention(Base):
    """
    Interventions (drugs, devices, procedures) being tested in a trial.
    """
    __tablename__ = "trial_interventions"

    id = Column(Integer, primary_key=True, index=True)
    trial_id = Column(Integer, ForeignKey("trials.id"), nullable=False, index=True)
    intervention_type = Column(SQLEnum(InterventionType), nullable=True)
    intervention_name = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    linked_drug_id = Column(Integer, ForeignKey("drugs.id"), nullable=True, index=True)  # Link to drugs table when possible
    
    # Relationships
    trial = relationship("Trial", back_populates="interventions")
    drug = relationship("Drug")


class TrialOutcome(Base):
    """
    Primary, secondary, and other outcome measures for a trial.
    """
    __tablename__ = "trial_outcomes"

    id = Column(Integer, primary_key=True, index=True)
    trial_id = Column(Integer, ForeignKey("trials.id"), nullable=False, index=True)
    outcome_type = Column(SQLEnum(OutcomeType), nullable=False, index=True)
    measure = Column(Text, nullable=False)
    time_frame = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    
    # Relationships
    trial = relationship("Trial", back_populates="outcomes")


class TrialResult(Base):
    """
    Trial results summary when available.
    """
    __tablename__ = "trial_results"

    id = Column(Integer, primary_key=True, index=True)
    trial_id = Column(Integer, ForeignKey("trials.id"), nullable=False, unique=True, index=True)
    results_available = Column(Boolean, default=False, index=True)
    results_url = Column(String(1000), nullable=True)
    results_first_posted_date = Column(Date, nullable=True)
    
    # Result summaries
    primary_outcome_summary = Column(Text, nullable=True)
    conclusion = Column(Text, nullable=True)
    reported_success_flag = Column(Boolean, nullable=True, index=True)  # Positive vs negative outcome
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    trial = relationship("Trial", back_populates="results")


class Catalyst(Base):
    """
    Investment catalysts - key upcoming events for drugs, trials, or companies.
    """
    __tablename__ = "catalysts"

    id = Column(Integer, primary_key=True, index=True)
    
    # Can relate to a trial, drug, event, or company
    trial_id = Column(Integer, ForeignKey("trials.id"), nullable=True, index=True)
    drug_id = Column(Integer, ForeignKey("drugs.id"), nullable=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True, index=True)
    company_mapping_id = Column(Integer, ForeignKey("company_mappings.id"), nullable=True, index=True)
    
    catalyst_type = Column(SQLEnum(CatalystType), nullable=False, index=True)
    expected_date = Column(Date, nullable=True, index=True)
    probability_band = Column(SQLEnum(CatalystProbability), default=CatalystProbability.MEDIUM)
    
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    source_url = Column(String(1000), nullable=True)
    
    # For grouping and filtering
    disease_area = Column(String(255), nullable=True, index=True)
    therapeutic_area = Column(String(255), nullable=True, index=True)
    
    is_auto_generated = Column(Boolean, default=True)  # True if generated from trial/approval data, False if manual
    is_archived = Column(Boolean, default=False, index=True)  # True if catalyst is past and archived

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    trial = relationship("Trial")
    drug = relationship("Drug")
    event = relationship("Event")
    company = relationship("CompanyMapping")
