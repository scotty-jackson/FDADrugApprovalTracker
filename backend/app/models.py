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
    Pharmaceutical sponsors/companies that submit FDA applications.
    """
    __tablename__ = "sponsors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
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
    """
    __tablename__ = "company_mappings"

    id = Column(Integer, primary_key=True, index=True)
    sponsor_id = Column(Integer, ForeignKey("sponsors.id"), nullable=False)
    company_name = Column(String(255), nullable=False, index=True)
    ticker = Column(String(20), nullable=True, index=True)
    exchange = Column(String(20), nullable=True)  # e.g., NASDAQ, NYSE
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
