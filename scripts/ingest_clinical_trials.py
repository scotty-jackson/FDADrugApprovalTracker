#!/usr/bin/env python3
"""
ClinicalTrials.gov Data Ingestion Script

Fetches clinical trial data from ClinicalTrials.gov API v2 and populates the database.
This script is designed to be run manually or via cron for scheduled updates.

Data Source:
- ClinicalTrials.gov API v2 (https://clinicaltrials.gov/api/v2/)

Usage:
    python scripts/ingest_clinical_trials.py [--incremental] [--limit N] [--disease-area AREA]

Options:
    --incremental         Only fetch new/updated records since last run
    --limit N            Limit number of records to fetch (for testing)
    --disease-area AREA  Filter by disease area (e.g., "Oncology", "Neurology")
    --phase PHASE        Filter by phase (e.g., "Phase 3")
    --status STATUS      Filter by status (e.g., "Recruiting")
    --verbose            Enable verbose logging

Note: This script respects ClinicalTrials.gov rate limits and includes delays between requests.
"""
import sys
import os
import argparse
import time
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.app.database import SessionLocal
from backend.app.models import (
    Sponsor, Trial, TrialCondition, TrialIntervention, TrialOutcome, TrialResult,
    TrialPhase, TrialStatus, StudyType, InterventionType, OutcomeType
)
from backend.app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ClinicalTrialsIngester:
    """
    Handles fetching and ingesting clinical trial data from ClinicalTrials.gov API v2.
    """

    API_BASE_URL = "https://clinicaltrials.gov/api/v2"

    def __init__(self, db_session, delay_seconds: float = 0.5, max_retries: int = 3):
        self.db = db_session
        self.delay = delay_seconds
        self.session = self._create_session(max_retries)
        self.records_processed = 0
        self.records_skipped = 0
        self.errors = 0

    def _create_session(self, max_retries: int) -> requests.Session:
        """Create requests session with retry logic."""
        session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update({
            'User-Agent': 'FDADrugApprovalTracker/1.0 (Educational/Research Purpose)',
            'Accept': 'application/json'
        })
        return session

    def _delay_request(self):
        """Delay between requests to respect rate limits."""
        time.sleep(self.delay)

    def _get_or_create_sponsor(self, sponsor_name: str, sponsor_type: str = None) -> Sponsor:
        """Get existing sponsor or create new one."""
        if not sponsor_name:
            sponsor_name = "Unknown Sponsor"

        sponsor = self.db.query(Sponsor).filter(Sponsor.name == sponsor_name).first()
        if not sponsor:
            sponsor = Sponsor(
                name=sponsor_name,
                sponsor_type=sponsor_type or "unknown"
            )
            self.db.add(sponsor)
            self.db.flush()
            logger.debug(f"Created new sponsor: {sponsor_name}")
        return sponsor

    def _map_phase(self, phase_str: str) -> Optional[TrialPhase]:
        """Map ClinicalTrials.gov phase string to our enum."""
        if not phase_str:
            return None

        phase_mapping = {
            "EARLY_PHASE1": TrialPhase.EARLY_PHASE_1,
            "PHASE1": TrialPhase.PHASE_1,
            "PHASE2": TrialPhase.PHASE_2,
            "PHASE3": TrialPhase.PHASE_3,
            "PHASE4": TrialPhase.PHASE_4,
            "NA": TrialPhase.NOT_APPLICABLE,
            "NOT_APPLICABLE": TrialPhase.NOT_APPLICABLE,
        }

        # Clean the phase string
        clean_phase = phase_str.upper().replace(" ", "").replace("_", "")

        for key, value in phase_mapping.items():
            if clean_phase in key or key in clean_phase:
                return value

        logger.warning(f"Unknown phase: {phase_str}")
        return None

    def _map_status(self, status_str: str) -> Optional[TrialStatus]:
        """Map ClinicalTrials.gov status string to our enum."""
        if not status_str:
            return None

        status_mapping = {
            "RECRUITING": TrialStatus.RECRUITING,
            "ACTIVE_NOT_RECRUITING": TrialStatus.ACTIVE_NOT_RECRUITING,
            "NOT_YET_RECRUITING": TrialStatus.NOT_YET_RECRUITING,
            "ENROLLING_BY_INVITATION": TrialStatus.ENROLLING_BY_INVITATION,
            "COMPLETED": TrialStatus.COMPLETED,
            "SUSPENDED": TrialStatus.SUSPENDED,
            "TERMINATED": TrialStatus.TERMINATED,
            "WITHDRAWN": TrialStatus.WITHDRAWN,
            "UNKNOWN": TrialStatus.UNKNOWN_STATUS,
        }

        clean_status = status_str.upper().replace(" ", "_").replace(",", "")

        for key, value in status_mapping.items():
            if clean_status == key or clean_status in key:
                return value

        logger.warning(f"Unknown status: {status_str}")
        return TrialStatus.UNKNOWN_STATUS

    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string from ClinicalTrials.gov."""
        if not date_str:
            return None

        # Try different date formats
        formats = [
            "%Y-%m-%d",
            "%Y-%m",
            "%Y",
            "%B %d, %Y",
            "%B %Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        logger.warning(f"Could not parse date: {date_str}")
        return None

    def fetch_trials(
        self,
        query: Optional[str] = None,
        disease_area: Optional[str] = None,
        phase: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        incremental: bool = False
    ) -> int:
        """
        Fetch trials from ClinicalTrials.gov API v2.

        Args:
            query: Search query term
            disease_area: Filter by disease/condition
            phase: Filter by trial phase
            status: Filter by recruitment status
            limit: Maximum number of trials to fetch
            incremental: Only fetch trials updated in last 7 days

        Returns:
            Number of trials processed
        """
        logger.info("Fetching trials from ClinicalTrials.gov API...")

        # Build query parameters
        params = {
            "format": "json",
            "pageSize": min(100, limit) if limit else 100,
        }

        # Add filters
        filter_parts = []

        if disease_area:
            params["query.cond"] = disease_area

        if phase:
            params["query.phase"] = phase

        if status:
            params["filter.overallStatus"] = status

        if incremental:
            # Fetch only trials updated in last 7 days
            seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            params["filter.lastUpdatePostDate"] = f"{seven_days_ago}:MAX"

        # Fetch trials with pagination
        page_token = None
        total_fetched = 0

        while True:
            if limit and total_fetched >= limit:
                break

            if page_token:
                params["pageToken"] = page_token

            try:
                response = self.session.get(
                    f"{self.API_BASE_URL}/studies",
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()

            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching trials: {e}")
                break

            # Process studies
            studies = data.get("studies", [])
            if not studies:
                break

            logger.info(f"Processing page with {len(studies)} studies...")

            for study in studies:
                if limit and total_fetched >= limit:
                    break

                try:
                    self._process_trial(study)
                    total_fetched += 1

                    # Commit every 10 records
                    if total_fetched % 10 == 0:
                        self.db.commit()
                        logger.info(f"Progress: {total_fetched} trials processed")

                    self._delay_request()

                except Exception as e:
                    logger.error(f"Error processing trial: {e}")
                    self.errors += 1
                    continue

            # Check for next page
            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break

            page_token = next_page_token
            self._delay_request()

        # Final commit
        self.db.commit()

        logger.info(f"Successfully processed {self.records_processed} trials")
        logger.info(f"Skipped {self.records_skipped} existing trials")
        logger.info(f"Encountered {self.errors} errors")

        return self.records_processed

    def _process_trial(self, study_data: Dict[str, Any]):
        """
        Process a single trial record from API response.

        Expected structure from ClinicalTrials.gov API v2:
        {
            "protocolSection": {
                "identificationModule": {...},
                "statusModule": {...},
                "sponsorCollaboratorsModule": {...},
                "descriptionModule": {...},
                "conditionsModule": {...},
                "designModule": {...},
                "armsInterventionsModule": {...},
                "outcomesModule": {...},
                ...
            }
        }
        """
        protocol = study_data.get("protocolSection", {})

        # Get basic identification
        identification = protocol.get("identificationModule", {})
        nct_id = identification.get("nctId")

        if not nct_id:
            logger.warning("Trial missing NCT ID, skipping")
            return

        # Check if trial already exists
        existing = self.db.query(Trial).filter(Trial.registry_id == nct_id).first()

        # Get status info
        status_module = protocol.get("statusModule", {})
        overall_status = status_module.get("overallStatus")

        # Get design info
        design_module = protocol.get("designModule", {})
        design_info = design_module.get("designInfo", {})
        phases = design_info.get("phases", [])
        phase_str = phases[0] if phases else None

        study_type = design_module.get("studyType")

        # Get sponsor info
        sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
        lead_sponsor = sponsor_module.get("leadSponsor", {})
        sponsor_name = lead_sponsor.get("name", "Unknown")
        sponsor_class = lead_sponsor.get("class", "unknown")

        # Map sponsor class to our sponsor_type
        sponsor_type_mapping = {
            "INDUSTRY": "pharma",
            "NIH": "academic",
            "FED": "government",
            "OTHER_GOV": "government",
            "OTHER": "other",
            "INDIV": "other",
            "NETWORK": "other",
        }
        sponsor_type = sponsor_type_mapping.get(sponsor_class.upper(), "other")

        sponsor = self._get_or_create_sponsor(sponsor_name, sponsor_type)

        # Get dates
        start_date_struct = status_module.get("startDateStruct", {})
        start_date = self._parse_date(start_date_struct.get("date"))

        primary_completion_struct = status_module.get("primaryCompletionDateStruct", {})
        primary_completion_date = self._parse_date(primary_completion_struct.get("date"))

        completion_date_struct = status_module.get("completionDateStruct", {})
        completion_date = self._parse_date(completion_date_struct.get("date"))

        # Get description
        description_module = protocol.get("descriptionModule", {})
        brief_title = identification.get("briefTitle", "")
        official_title = identification.get("officialTitle", brief_title)
        brief_summary = description_module.get("briefSummary", "")

        # Create or update trial
        if existing:
            # Update existing trial
            trial = existing
            trial.title = official_title
            trial.status = self._map_status(overall_status)
            trial.phase = self._map_phase(phase_str)
            trial.start_date = start_date
            trial.primary_completion_date = primary_completion_date
            trial.completion_date = completion_date
            trial.brief_summary = brief_summary
            trial.sponsor_id = sponsor.id
            trial.last_updated = datetime.now()

            self.records_skipped += 1
            logger.debug(f"Updated existing trial: {nct_id}")
        else:
            # Create new trial
            trial = Trial(
                registry="ClinicalTrials.gov",
                registry_id=nct_id,
                title=official_title,
                status=self._map_status(overall_status),
                phase=self._map_phase(phase_str),
                study_type=StudyType.INTERVENTIONAL if study_type == "INTERVENTIONAL" else StudyType.OBSERVATIONAL,
                start_date=start_date,
                primary_completion_date=primary_completion_date,
                completion_date=completion_date,
                enrollment=status_module.get("enrollmentInfo", {}).get("count"),
                brief_summary=brief_summary,
                sponsor_id=sponsor.id,
                source_url=f"https://clinicaltrials.gov/study/{nct_id}"
            )
            self.db.add(trial)
            self.db.flush()

            self.records_processed += 1
            logger.debug(f"Created new trial: {nct_id}")

        # Process conditions
        self._process_conditions(trial, protocol.get("conditionsModule", {}))

        # Process interventions
        self._process_interventions(trial, protocol.get("armsInterventionsModule", {}))

        # Process outcomes
        self._process_outcomes(trial, protocol.get("outcomesModule", {}))

    def _process_conditions(self, trial: Trial, conditions_module: Dict[str, Any]):
        """Process trial conditions/diseases."""
        conditions = conditions_module.get("conditions", [])

        # Remove existing conditions if updating
        self.db.query(TrialCondition).filter(TrialCondition.trial_id == trial.id).delete()

        for condition_name in conditions:
            # Try to map to disease area
            disease_area = self._map_condition_to_disease_area(condition_name)

            condition = TrialCondition(
                trial_id=trial.id,
                condition_name=condition_name,
                disease_area=disease_area
            )
            self.db.add(condition)

    def _map_condition_to_disease_area(self, condition: str) -> Optional[str]:
        """Map condition to broader disease area."""
        condition_lower = condition.lower()

        # Simple mapping - in production, use a more comprehensive mapping
        disease_area_keywords = {
            "Oncology": ["cancer", "tumor", "carcinoma", "melanoma", "leukemia", "lymphoma", "sarcoma", "oncology"],
            "Neurology": ["alzheimer", "parkinson", "dementia", "neurology", "neurological", "brain", "seizure", "epilepsy"],
            "Cardiology": ["heart", "cardiac", "cardiovascular", "hypertension", "arrhythmia"],
            "Immunology": ["immune", "autoimmune", "immunology", "lupus", "arthritis"],
            "Infectious Disease": ["infection", "infectious", "virus", "bacterial", "hiv", "hepatitis"],
            "Endocrinology": ["diabetes", "thyroid", "endocrine", "hormone"],
            "Respiratory": ["asthma", "copd", "lung", "respiratory", "pulmonary"],
            "Gastroenterology": ["crohn", "colitis", "gastro", "liver", "hepatic", "nash", "nafld"],
            "Ophthalmology": ["eye", "vision", "ophthalm", "retina", "macular"],
            "Rare Disease": ["rare disease", "orphan"],
        }

        for disease_area, keywords in disease_area_keywords.items():
            for keyword in keywords:
                if keyword in condition_lower:
                    return disease_area

        return "Other"

    def _process_interventions(self, trial: Trial, arms_module: Dict[str, Any]):
        """Process trial interventions/drugs."""
        interventions = arms_module.get("interventions", [])

        # Remove existing interventions if updating
        self.db.query(TrialIntervention).filter(TrialIntervention.trial_id == trial.id).delete()

        for intervention_data in interventions:
            intervention_type_str = intervention_data.get("type", "").upper()

            # Map intervention type
            intervention_type = None
            if "DRUG" in intervention_type_str:
                intervention_type = InterventionType.DRUG
            elif "BIOLOGICAL" in intervention_type_str or "BIOLOGIC" in intervention_type_str:
                intervention_type = InterventionType.BIOLOGICAL
            elif "DEVICE" in intervention_type_str:
                intervention_type = InterventionType.DEVICE
            elif "PROCEDURE" in intervention_type_str:
                intervention_type = InterventionType.PROCEDURE
            elif "BEHAVIORAL" in intervention_type_str:
                intervention_type = InterventionType.BEHAVIORAL
            else:
                intervention_type = InterventionType.OTHER

            intervention = TrialIntervention(
                trial_id=trial.id,
                intervention_type=intervention_type,
                intervention_name=intervention_data.get("name", ""),
                description=intervention_data.get("description")
            )
            self.db.add(intervention)

    def _process_outcomes(self, trial: Trial, outcomes_module: Dict[str, Any]):
        """Process trial outcome measures."""
        primary_outcomes = outcomes_module.get("primaryOutcomes", [])
        secondary_outcomes = outcomes_module.get("secondaryOutcomes", [])

        # Remove existing outcomes if updating
        self.db.query(TrialOutcome).filter(TrialOutcome.trial_id == trial.id).delete()

        for outcome_data in primary_outcomes:
            outcome = TrialOutcome(
                trial_id=trial.id,
                outcome_type=OutcomeType.PRIMARY,
                outcome_measure=outcome_data.get("measure", ""),
                time_frame=outcome_data.get("timeFrame")
            )
            self.db.add(outcome)

        for outcome_data in secondary_outcomes:
            outcome = TrialOutcome(
                trial_id=trial.id,
                outcome_type=OutcomeType.SECONDARY,
                outcome_measure=outcome_data.get("measure", ""),
                time_frame=outcome_data.get("timeFrame")
            )
            self.db.add(outcome)


def main():
    """Main entry point for clinical trials data ingestion."""
    parser = argparse.ArgumentParser(description='Ingest clinical trial data from ClinicalTrials.gov')
    parser.add_argument('--incremental', action='store_true',
                        help='Only fetch trials updated in last 7 days')
    parser.add_argument('--limit', type=int, default=None,
                        help='Limit number of trials to fetch')
    parser.add_argument('--disease-area', type=str, default=None,
                        help='Filter by disease area (e.g., "Cancer", "Diabetes")')
    parser.add_argument('--phase', type=str, default=None,
                        help='Filter by phase (e.g., "Phase 3")')
    parser.add_argument('--status', type=str, default=None,
                        help='Filter by status (e.g., "Recruiting")')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("=" * 60)
    logger.info("ClinicalTrials.gov Data Ingestion Started")
    logger.info("=" * 60)

    db = SessionLocal()

    try:
        ingester = ClinicalTrialsIngester(db)

        # Fetch trials
        trials_count = ingester.fetch_trials(
            disease_area=args.disease_area,
            phase=args.phase,
            status=args.status,
            limit=args.limit,
            incremental=args.incremental
        )

        logger.info("=" * 60)
        logger.info(f"✓ Processed {trials_count} clinical trials")
        logger.info("ClinicalTrials.gov Data Ingestion Completed Successfully")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"✗ Fatal error during ingestion: {e}", exc_info=True)
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
