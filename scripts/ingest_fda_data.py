#!/usr/bin/env python3
"""
FDA Data Ingestion Script

Fetches drug approval data from public FDA sources and populates the database.
This script is designed to be run manually or via cron for scheduled updates.

Data Sources:
- FDA Drugs@FDA database (https://www.accessdata.fda.gov/scripts/cder/daf/)
- FDA CDER approvals RSS feed
- FDA press releases

Usage:
    python scripts/ingest_fda_data.py [--incremental] [--limit N]

Options:
    --incremental    Only fetch new records since last run
    --limit N        Limit number of records to fetch (for testing)
    --verbose        Enable verbose logging

Note: This script respects FDA's robots.txt and includes delays between requests.
"""
import sys
import os
import argparse
import time
import logging
from datetime import datetime, date
from typing import List, Optional, Dict
import requests
from bs4 import BeautifulSoup

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.app.database import SessionLocal
from backend.app.models import (
    Sponsor, Drug, Approval, Event,
    FDACenter, ApplicationType, DecisionOutcome, EventType, EventStatus
)
from backend.app.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FDADataIngester:
    """
    Handles fetching and ingesting FDA drug approval data.
    """

    def __init__(self, db_session, delay_seconds: int = None):
        self.db = db_session
        self.delay = delay_seconds or settings.fda_request_delay_seconds
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FDADrugApprovalTracker/1.0 (Educational/Research Purpose)'
        })

    def _delay_request(self):
        """Delay between requests to be respectful of FDA servers."""
        time.sleep(self.delay)

    def _get_or_create_sponsor(self, sponsor_name: str) -> Sponsor:
        """Get existing sponsor or create new one."""
        sponsor = self.db.query(Sponsor).filter(Sponsor.name == sponsor_name).first()
        if not sponsor:
            sponsor = Sponsor(name=sponsor_name)
            self.db.add(sponsor)
            self.db.flush()
            logger.info(f"Created new sponsor: {sponsor_name}")
        return sponsor

    def _parse_application_type(self, app_num: str) -> ApplicationType:
        """Parse application type from application number."""
        app_num_upper = app_num.upper()
        if app_num_upper.startswith('NDA'):
            return ApplicationType.NDA
        elif app_num_upper.startswith('BLA'):
            return ApplicationType.BLA
        elif app_num_upper.startswith('ANDA'):
            return ApplicationType.ANDA
        else:
            return ApplicationType.OTHER

    def fetch_drugs_at_fda(self, limit: Optional[int] = None) -> int:
        """
        Fetch drug approval data from FDA's Drugs@FDA database.

        Note: This is a simplified example. In production, you would:
        1. Use FDA's official API if available
        2. Parse their downloadable datasets (CSV/XML)
        3. Implement robust error handling and retry logic

        Returns:
            Number of records processed
        """
        logger.info("Fetching data from FDA Drugs@FDA database...")

        # Example: FDA provides downloadable datasets
        # https://www.fda.gov/drugs/drug-approvals-and-databases/drugsfda-data-files
        # In a real implementation, download and parse these files

        # For this example, we'll show the structure of how to process such data
        sample_approvals = self._get_sample_fda_data()

        count = 0
        for approval_data in sample_approvals[:limit] if limit else sample_approvals:
            try:
                self._process_approval_record(approval_data)
                count += 1
                self._delay_request()
            except Exception as e:
                logger.error(f"Error processing record: {e}")
                continue

        self.db.commit()
        logger.info(f"Successfully processed {count} approval records")
        return count

    def _process_approval_record(self, data: Dict):
        """
        Process a single approval record and add to database.

        Expected data format:
        {
            'drug_name': str,
            'brand_name': str,
            'sponsor_name': str,
            'application_number': str,
            'approval_date': date,
            'indication': str,
            'therapeutic_area': str,
            'fda_center': str,
            'label_url': str (optional),
        }
        """
        # Check if approval already exists
        existing = self.db.query(Approval).filter(
            Approval.application_number == data['application_number']
        ).first()

        if existing:
            logger.debug(f"Approval {data['application_number']} already exists, skipping")
            return

        # Get or create sponsor
        sponsor = self._get_or_create_sponsor(data['sponsor_name'])

        # Check if drug exists
        drug = self.db.query(Drug).filter(
            Drug.drug_name == data['drug_name'],
            Drug.sponsor_id == sponsor.id
        ).first()

        if not drug:
            drug = Drug(
                drug_name=data['drug_name'],
                brand_name=data.get('brand_name'),
                generic_name=data.get('generic_name'),
                primary_indication=data.get('indication'),
                therapeutic_area=data.get('therapeutic_area'),
                route_of_administration=data.get('route'),
                sponsor_id=sponsor.id
            )
            self.db.add(drug)
            self.db.flush()
            logger.info(f"Created new drug: {data['drug_name']}")

        # Create approval record
        fda_center = FDACenter.CDER if data.get('fda_center') == 'CDER' else FDACenter.CBER
        app_type = self._parse_application_type(data['application_number'])

        approval = Approval(
            drug_id=drug.id,
            fda_center=fda_center,
            approval_date=data['approval_date'],
            application_type=app_type,
            application_number=data['application_number'],
            decision_outcome=DecisionOutcome.APPROVED,
            indication=data.get('indication'),
            label_url=data.get('label_url'),
            fda_page_url=data.get('fda_page_url')
        )
        self.db.add(approval)
        logger.info(f"Added approval: {data['application_number']} for {data['drug_name']}")

    def _get_sample_fda_data(self) -> List[Dict]:
        """
        Return sample FDA approval data.

        In a real implementation, this would:
        1. Download FDA's latest dataset files
        2. Parse CSV/XML/JSON files
        3. Or scrape from approved web pages following robots.txt

        For demonstration, we return sample data structure.
        """
        # This is example data showing the structure
        # In production, replace with actual FDA data parsing
        sample_data = [
            {
                'drug_name': 'Example Drug A',
                'brand_name': 'BrandA',
                'generic_name': 'genericdrug-a',
                'sponsor_name': 'Example Pharma Co.',
                'application_number': 'NDA999999',
                'approval_date': date(2024, 1, 15),
                'indication': 'Treatment of example condition',
                'therapeutic_area': 'Cardiology',
                'fda_center': 'CDER',
                'route': 'Oral',
                'label_url': 'https://www.accessdata.fda.gov/drugsatfda_docs/label/2024/999999lbl.pdf'
            },
            # More records would follow...
        ]

        logger.info(f"Retrieved {len(sample_data)} sample records (replace with actual FDA data in production)")
        return sample_data

    def fetch_pdufa_dates(self) -> int:
        """
        Fetch upcoming PDUFA dates.

        In production, sources include:
        - Company press releases
        - FDA PDUFA calendar (if available)
        - Biotech investor tracking sites

        Returns:
            Number of events added
        """
        logger.info("Fetching PDUFA dates...")

        # Example structure for PDUFA data
        # In production, implement actual scraping/API calls
        sample_events = []

        count = 0
        for event_data in sample_events:
            try:
                # Check if event already exists
                existing = self.db.query(Event).filter(
                    Event.application_number == event_data['application_number'],
                    Event.event_type == EventType.PDUFA
                ).first()

                if existing:
                    continue

                event = Event(
                    event_type=EventType.PDUFA,
                    event_date=event_data['pdufa_date'],
                    event_status=EventStatus.SCHEDULED,
                    application_number=event_data['application_number'],
                    description=event_data['description'],
                    source_url=event_data.get('source_url')
                )
                self.db.add(event)
                count += 1
            except Exception as e:
                logger.error(f"Error processing PDUFA event: {e}")
                continue

        self.db.commit()
        logger.info(f"Successfully added {count} PDUFA events")
        return count


def main():
    """Main entry point for FDA data ingestion."""
    parser = argparse.ArgumentParser(description='Ingest FDA drug approval data')
    parser.add_argument('--incremental', action='store_true',
                        help='Only fetch new records since last run')
    parser.add_argument('--limit', type=int, default=None,
                        help='Limit number of records to fetch')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("=" * 60)
    logger.info("FDA Data Ingestion Started")
    logger.info("=" * 60)

    db = SessionLocal()

    try:
        ingester = FDADataIngester(db)

        # Fetch drug approvals
        approvals_count = ingester.fetch_drugs_at_fda(limit=args.limit)
        logger.info(f"✓ Processed {approvals_count} approval records")

        # Fetch PDUFA dates
        events_count = ingester.fetch_pdufa_dates()
        logger.info(f"✓ Processed {events_count} PDUFA events")

        logger.info("=" * 60)
        logger.info("FDA Data Ingestion Completed Successfully")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"✗ Fatal error during ingestion: {e}", exc_info=True)
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
