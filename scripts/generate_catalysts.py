#!/usr/bin/env python3
"""
Catalyst Generation Script

Automatically generates investment catalysts from:
1. Clinical trial primary completion dates (topline readouts)
2. FDA PDUFA dates
3. Advisory Committee meetings
4. Other regulatory events

Catalysts are key upcoming events that could move stock prices for biotech/pharma companies.

Usage:
    python scripts/generate_catalysts.py [--regenerate] [--lookback-days N]

Options:
    --regenerate      Delete and regenerate all catalysts
    --lookback-days   Days to look back for trial data (default: 365)
    --lookahead-days  Days to look ahead for catalysts (default: 730)
    --verbose         Enable verbose logging
"""
import sys
import os
import argparse
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict
from sqlalchemy import and_, or_

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.app.database import SessionLocal
from backend.app.models import (
    Trial, TrialStatus, TrialPhase, Event, EventType, EventStatus,
    Drug, Catalyst, CatalystType, CatalystProbability,
    CompanyMapping, Sponsor
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CatalystGenerator:
    """
    Generates investment catalysts from trials and regulatory events.
    """

    def __init__(self, db_session):
        self.db = db_session
        self.catalysts_created = 0
        self.catalysts_updated = 0
        self.catalysts_skipped = 0

    def generate_all_catalysts(
        self,
        regenerate: bool = False,
        lookback_days: int = 365,
        lookahead_days: int = 730
    ) -> Dict[str, int]:
        """
        Generate all catalysts from trials and events.

        Args:
            regenerate: If True, delete and regenerate all catalysts
            lookback_days: Days to look back for trial data
            lookahead_days: Days to look ahead for future catalysts

        Returns:
            Dictionary with counts of catalysts created/updated
        """
        if regenerate:
            logger.info("Regenerating all catalysts (deleting existing)...")
            self.db.query(Catalyst).delete()
            self.db.commit()

        # Generate catalysts from trials
        self._generate_trial_catalysts(lookback_days, lookahead_days)

        # Generate catalysts from FDA events
        self._generate_fda_event_catalysts(lookahead_days)

        self.db.commit()

        return {
            "created": self.catalysts_created,
            "updated": self.catalysts_updated,
            "skipped": self.catalysts_skipped
        }

    def _generate_trial_catalysts(self, lookback_days: int, lookahead_days: int):
        """Generate catalysts from clinical trial completion dates."""
        logger.info("Generating catalysts from clinical trials...")

        today = date.today()
        lookback_date = today - timedelta(days=lookback_days)
        lookahead_date = today + timedelta(days=lookahead_days)

        # Find trials with upcoming primary completion dates
        trials = self.db.query(Trial).filter(
            and_(
                Trial.primary_completion_date.isnot(None),
                Trial.primary_completion_date >= today,
                Trial.primary_completion_date <= lookahead_date,
                Trial.status.in_([
                    TrialStatus.RECRUITING,
                    TrialStatus.ACTIVE_NOT_RECRUITING,
                    TrialStatus.ENROLLING_BY_INVITATION
                ])
            )
        ).all()

        logger.info(f"Found {len(trials)} trials with upcoming primary completion dates")

        for trial in trials:
            try:
                self._create_trial_catalyst(trial)
            except Exception as e:
                logger.error(f"Error creating catalyst for trial {trial.registry_id}: {e}")
                continue

    def _create_trial_catalyst(self, trial: Trial):
        """Create catalyst from a trial's primary completion date."""
        # Determine catalyst type based on phase
        if trial.phase in [TrialPhase.PHASE_3, TrialPhase.PHASE_4]:
            catalyst_type = CatalystType.TOPLINE_READOUT
        else:
            catalyst_type = CatalystType.PRIMARY_COMPLETION

        # Determine probability based on trial status and phase
        probability = self._calculate_trial_probability(trial)

        # Check if catalyst already exists
        existing = self.db.query(Catalyst).filter(
            and_(
                Catalyst.trial_id == trial.id,
                Catalyst.catalyst_type == catalyst_type
            )
        ).first()

        # Get company mapping for this trial's sponsor
        company_mapping = self.db.query(CompanyMapping).filter(
            CompanyMapping.sponsor_id == trial.sponsor_id
        ).first()

        if existing:
            # Update existing catalyst
            existing.expected_date = trial.primary_completion_date
            existing.probability_band = probability
            existing.company_mapping_id = company_mapping.id if company_mapping else None
            existing.title = self._generate_trial_title(trial)
            existing.description = self._generate_trial_description(trial)
            existing.updated_at = datetime.now()

            self.catalysts_updated += 1
            logger.debug(f"Updated catalyst for trial {trial.registry_id}")
        else:
            # Create new catalyst
            catalyst = Catalyst(
                trial_id=trial.id,
                drug_id=None,  # Will be linked if we can match drug name
                company_mapping_id=company_mapping.id if company_mapping else None,
                catalyst_type=catalyst_type,
                expected_date=trial.primary_completion_date,
                probability_band=probability,
                title=self._generate_trial_title(trial),
                description=self._generate_trial_description(trial),
                is_auto_generated=True
            )
            self.db.add(catalyst)
            self.catalysts_created += 1
            logger.debug(f"Created catalyst for trial {trial.registry_id}")

    def _calculate_trial_probability(self, trial: Trial) -> CatalystProbability:
        """
        Calculate probability band for a trial catalyst.

        Factors:
        - Trial phase (later phase = higher probability)
        - Trial status (active not recruiting = very high probability)
        - Time to completion (closer = higher probability)
        """
        if trial.status == TrialStatus.ACTIVE_NOT_RECRUITING:
            # Trial is actively running but not recruiting = very high probability
            return CatalystProbability.VERY_HIGH

        if trial.phase in [TrialPhase.PHASE_3, TrialPhase.PHASE_4]:
            # Check time to completion
            if trial.primary_completion_date:
                days_until = (trial.primary_completion_date - date.today()).days
                if days_until < 90:
                    return CatalystProbability.VERY_HIGH
                elif days_until < 180:
                    return CatalystProbability.HIGH
                else:
                    return CatalystProbability.MEDIUM

        if trial.phase == TrialPhase.PHASE_2:
            return CatalystProbability.MEDIUM

        if trial.phase in [TrialPhase.PHASE_1, TrialPhase.EARLY_PHASE_1]:
            return CatalystProbability.LOW

        return CatalystProbability.MEDIUM

    def _generate_trial_title(self, trial: Trial) -> str:
        """Generate a title for a trial catalyst."""
        phase_str = trial.phase.value if trial.phase else "Trial"

        # Get first intervention if available
        interventions = [i.intervention_name for i in trial.interventions[:1]]
        intervention_str = interventions[0] if interventions else "Drug Candidate"

        return f"{phase_str} Data: {intervention_str}"

    def _generate_trial_description(self, trial: Trial) -> str:
        """Generate a description for a trial catalyst."""
        phase_str = trial.phase.value if trial.phase else "clinical trial"

        # Get first condition if available
        conditions = [c.condition_name for c in trial.conditions[:2]]
        condition_str = ", ".join(conditions) if conditions else "multiple indications"

        # Get first intervention if available
        interventions = [i.intervention_name for i in trial.interventions[:2]]
        intervention_str = ", ".join(interventions) if interventions else "investigational therapy"

        return (
            f"{phase_str} primary completion for {intervention_str} "
            f"in {condition_str} ({trial.registry_id})"
        )

    def _generate_fda_event_catalysts(self, lookahead_days: int):
        """Generate catalysts from FDA regulatory events."""
        logger.info("Generating catalysts from FDA events...")

        today = date.today()
        lookahead_date = today + timedelta(days=lookahead_days)

        # Find upcoming FDA events
        events = self.db.query(Event).filter(
            and_(
                Event.event_date.isnot(None),
                Event.event_date >= today,
                Event.event_date <= lookahead_date,
                Event.event_status == EventStatus.SCHEDULED
            )
        ).all()

        logger.info(f"Found {len(events)} upcoming FDA events")

        for event in events:
            try:
                self._create_event_catalyst(event)
            except Exception as e:
                logger.error(f"Error creating catalyst for event {event.id}: {e}")
                continue

    def _create_event_catalyst(self, event: Event):
        """Create catalyst from an FDA event."""
        # Map event type to catalyst type
        catalyst_type_mapping = {
            EventType.PDUFA: CatalystType.PDUFA_DATE,
            EventType.ADCOM: CatalystType.ADCOM_MEETING,
            EventType.FDA_DECISION: CatalystType.FDA_DECISION,
            EventType.APPROVAL: CatalystType.FDA_DECISION,
        }

        catalyst_type = catalyst_type_mapping.get(event.event_type, CatalystType.OTHER_REGULATORY)

        # Check if catalyst already exists
        existing = self.db.query(Catalyst).filter(
            and_(
                Catalyst.event_id == event.id,
                Catalyst.catalyst_type == catalyst_type
            )
        ).first()

        # Find drug and company for this event
        drug = None
        company_mapping = None

        if event.drug_id:
            drug = self.db.query(Drug).filter(Drug.id == event.drug_id).first()
            if drug and drug.sponsor_id:
                company_mapping = self.db.query(CompanyMapping).filter(
                    CompanyMapping.sponsor_id == drug.sponsor_id
                ).first()

        # Probability is very high for scheduled FDA events
        probability = CatalystProbability.VERY_HIGH

        if existing:
            # Update existing catalyst
            existing.expected_date = event.event_date
            existing.probability_band = probability
            existing.drug_id = drug.id if drug else None
            existing.company_mapping_id = company_mapping.id if company_mapping else None
            existing.title = self._generate_event_title(event, drug)
            existing.description = self._generate_event_description(event, drug)
            existing.updated_at = datetime.now()

            self.catalysts_updated += 1
            logger.debug(f"Updated catalyst for event {event.id}")
        else:
            # Create new catalyst
            catalyst = Catalyst(
                event_id=event.id,
                drug_id=drug.id if drug else None,
                trial_id=None,
                company_mapping_id=company_mapping.id if company_mapping else None,
                catalyst_type=catalyst_type,
                expected_date=event.event_date,
                probability_band=probability,
                title=self._generate_event_title(event, drug),
                description=self._generate_event_description(event, drug),
                is_auto_generated=True
            )
            self.db.add(catalyst)
            self.catalysts_created += 1
            logger.debug(f"Created catalyst for event {event.id}")

    def _generate_event_title(self, event: Event, drug: Optional[Drug]) -> str:
        """Generate a title for an event catalyst."""
        drug_name = drug.drug_name if drug else "Drug Candidate"
        event_type_str = event.event_type.value
        return f"{event_type_str}: {drug_name}"

    def _generate_event_description(self, event: Event, drug: Optional[Drug]) -> str:
        """Generate a description for an event catalyst."""
        drug_name = drug.drug_name if drug else "drug candidate"
        event_type_str = event.event_type.value

        if event.description:
            return f"{event_type_str}: {event.description}"
        else:
            return f"{event_type_str} for {drug_name}"

    def archive_past_catalysts(self, days_old: int = 30):
        """
        Archive catalysts that are past their expected date.

        Args:
            days_old: Archive catalysts older than this many days
        """
        logger.info(f"Archiving catalysts older than {days_old} days...")

        cutoff_date = date.today() - timedelta(days=days_old)

        past_catalysts = self.db.query(Catalyst).filter(
            and_(
                Catalyst.expected_date.isnot(None),
                Catalyst.expected_date < cutoff_date,
                Catalyst.is_archived == False
            )
        ).all()

        for catalyst in past_catalysts:
            catalyst.is_archived = True

        self.db.commit()
        logger.info(f"Archived {len(past_catalysts)} past catalysts")

        return len(past_catalysts)

    def update_catalyst_probabilities(self):
        """
        Update probability bands for existing catalysts based on current trial/event status.
        """
        logger.info("Updating catalyst probabilities...")

        # Get all active catalysts
        active_catalysts = self.db.query(Catalyst).filter(
            and_(
                Catalyst.is_archived == False,
                Catalyst.expected_date >= date.today()
            )
        ).all()

        updated_count = 0

        for catalyst in active_catalysts:
            old_probability = catalyst.probability_band

            if catalyst.trial_id:
                trial = self.db.query(Trial).filter(Trial.id == catalyst.trial_id).first()
                if trial:
                    new_probability = self._calculate_trial_probability(trial)

                    # Also check if trial status changed to completed/terminated
                    if trial.status in [TrialStatus.COMPLETED, TrialStatus.TERMINATED, TrialStatus.WITHDRAWN]:
                        catalyst.is_archived = True
                        logger.debug(f"Archived catalyst for {trial.status.value} trial {trial.registry_id}")
                    elif new_probability != old_probability:
                        catalyst.probability_band = new_probability
                        updated_count += 1
                        logger.debug(
                            f"Updated probability for trial {trial.registry_id}: "
                            f"{old_probability.value} -> {new_probability.value}"
                        )

        self.db.commit()
        logger.info(f"Updated probabilities for {updated_count} catalysts")

        return updated_count


def main():
    """Main entry point for catalyst generation."""
    parser = argparse.ArgumentParser(description='Generate investment catalysts from trials and events')
    parser.add_argument('--regenerate', action='store_true',
                        help='Delete and regenerate all catalysts')
    parser.add_argument('--lookback-days', type=int, default=365,
                        help='Days to look back for trial data (default: 365)')
    parser.add_argument('--lookahead-days', type=int, default=730,
                        help='Days to look ahead for catalysts (default: 730)')
    parser.add_argument('--archive-old', action='store_true',
                        help='Archive past catalysts')
    parser.add_argument('--update-probabilities', action='store_true',
                        help='Update probability bands for existing catalysts')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("=" * 60)
    logger.info("Catalyst Generation Started")
    logger.info("=" * 60)

    db = SessionLocal()

    try:
        generator = CatalystGenerator(db)

        # Generate catalysts
        stats = generator.generate_all_catalysts(
            regenerate=args.regenerate,
            lookback_days=args.lookback_days,
            lookahead_days=args.lookahead_days
        )

        logger.info(f"✓ Created {stats['created']} new catalysts")
        logger.info(f"✓ Updated {stats['updated']} existing catalysts")
        logger.info(f"✓ Skipped {stats['skipped']} catalysts")

        # Archive old catalysts if requested
        if args.archive_old:
            archived = generator.archive_past_catalysts()
            logger.info(f"✓ Archived {archived} past catalysts")

        # Update probabilities if requested
        if args.update_probabilities:
            updated = generator.update_catalyst_probabilities()
            logger.info(f"✓ Updated probabilities for {updated} catalysts")

        logger.info("=" * 60)
        logger.info("Catalyst Generation Completed Successfully")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"✗ Fatal error during catalyst generation: {e}", exc_info=True)
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
