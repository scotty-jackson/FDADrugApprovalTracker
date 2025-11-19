#!/usr/bin/env python3
"""
Seed database with sample FDA drug approval data.
This provides initial data for testing and demonstration purposes.

Usage:
    python scripts/seed_data.py
"""
import sys
import os
from datetime import datetime, date, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.app.database import SessionLocal
from backend.app.models import (
    Sponsor, Drug, Approval, Event, CompanyMapping,
    FDACenter, ApplicationType, DecisionOutcome, EventType, EventStatus
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_database():
    """Populate database with sample data."""
    db = SessionLocal()

    try:
        logger.info("Starting database seeding...")

        # Check if data already exists
        if db.query(Sponsor).count() > 0:
            logger.warning("Database already contains data. Skipping seed.")
            return

        # Create sponsors
        pfizer = Sponsor(name="Pfizer Inc.")
        moderna = Sponsor(name="Moderna, Inc.")
        jnj = Sponsor(name="Johnson & Johnson")
        merck = Sponsor(name="Merck & Co., Inc.")
        regeneron = Sponsor(name="Regeneron Pharmaceuticals, Inc.")
        biogen = Sponsor(name="Biogen Inc.")
        gilead = Sponsor(name="Gilead Sciences, Inc.")

        db.add_all([pfizer, moderna, jnj, merck, regeneron, biogen, gilead])
        db.commit()

        logger.info("✓ Created sponsors")

        # Create company mappings
        mappings = [
            CompanyMapping(sponsor=pfizer, company_name="Pfizer Inc.", ticker="PFE", exchange="NYSE"),
            CompanyMapping(sponsor=moderna, company_name="Moderna, Inc.", ticker="MRNA", exchange="NASDAQ"),
            CompanyMapping(sponsor=jnj, company_name="Johnson & Johnson", ticker="JNJ", exchange="NYSE"),
            CompanyMapping(sponsor=merck, company_name="Merck & Co., Inc.", ticker="MRK", exchange="NYSE"),
            CompanyMapping(sponsor=regeneron, company_name="Regeneron Pharmaceuticals, Inc.", ticker="REGN", exchange="NASDAQ"),
            CompanyMapping(sponsor=biogen, company_name="Biogen Inc.", ticker="BIIB", exchange="NASDAQ"),
            CompanyMapping(sponsor=gilead, company_name="Gilead Sciences, Inc.", ticker="GILD", exchange="NASDAQ"),
        ]
        db.add_all(mappings)
        db.commit()

        logger.info("✓ Created company mappings")

        # Create sample drugs and approvals
        drugs_data = [
            {
                "drug": Drug(
                    drug_name="Paxlovid",
                    brand_name="Paxlovid",
                    generic_name="nirmatrelvir and ritonavir",
                    primary_indication="Treatment of COVID-19 in adults and pediatric patients",
                    therapeutic_area="Infectious Disease",
                    route_of_administration="Oral",
                    sponsor=pfizer
                ),
                "approval": Approval(
                    fda_center=FDACenter.CDER,
                    approval_date=date(2023, 5, 25),
                    application_type=ApplicationType.NDA,
                    application_number="NDA217188",
                    decision_outcome=DecisionOutcome.APPROVED,
                    indication="Treatment of mild-to-moderate COVID-19",
                    fda_page_url="https://www.fda.gov/drugs/news-events-human-drugs/fda-approves-first-covid-19-oral-antiviral-treatment-high-risk-adults"
                )
            },
            {
                "drug": Drug(
                    drug_name="Spikevax",
                    brand_name="Spikevax",
                    generic_name="COVID-19 Vaccine, mRNA",
                    primary_indication="Prevention of COVID-19",
                    therapeutic_area="Vaccines",
                    route_of_administration="Intramuscular injection",
                    sponsor=moderna
                ),
                "approval": Approval(
                    fda_center=FDACenter.CBER,
                    approval_date=date(2022, 1, 31),
                    application_type=ApplicationType.BLA,
                    application_number="BLA125742",
                    decision_outcome=DecisionOutcome.APPROVED,
                    indication="Prevention of COVID-19 in individuals 18 years of age and older",
                    fda_page_url="https://www.fda.gov/vaccines-blood-biologics/spikevax"
                )
            },
            {
                "drug": Drug(
                    drug_name="Keytruda",
                    brand_name="Keytruda",
                    generic_name="pembrolizumab",
                    primary_indication="Treatment of various cancers",
                    therapeutic_area="Oncology",
                    route_of_administration="Intravenous",
                    sponsor=merck
                ),
                "approval": Approval(
                    fda_center=FDACenter.CDER,
                    approval_date=date(2014, 9, 4),
                    application_type=ApplicationType.BLA,
                    application_number="BLA125514",
                    decision_outcome=DecisionOutcome.APPROVED,
                    indication="Treatment of advanced melanoma",
                    fda_page_url="https://www.fda.gov/drugs/resources-information-approved-drugs"
                )
            },
            {
                "drug": Drug(
                    drug_name="Eylea HD",
                    brand_name="Eylea HD",
                    generic_name="aflibercept",
                    primary_indication="Treatment of wet age-related macular degeneration",
                    therapeutic_area="Ophthalmology",
                    route_of_administration="Intravitreal injection",
                    sponsor=regeneron
                ),
                "approval": Approval(
                    fda_center=FDACenter.CBER,
                    approval_date=date(2023, 8, 18),
                    application_type=ApplicationType.BLA,
                    application_number="BLA761307",
                    decision_outcome=DecisionOutcome.APPROVED,
                    indication="Treatment of wet AMD, diabetic macular edema, and diabetic retinopathy",
                    fda_page_url="https://www.fda.gov/drugs/news-events-human-drugs"
                )
            },
            {
                "drug": Drug(
                    drug_name="Leqembi",
                    brand_name="Leqembi",
                    generic_name="lecanemab-irmb",
                    primary_indication="Treatment of Alzheimer's disease",
                    therapeutic_area="Neurology",
                    route_of_administration="Intravenous infusion",
                    sponsor=biogen
                ),
                "approval": Approval(
                    fda_center=FDACenter.CDER,
                    approval_date=date(2023, 7, 6),
                    application_type=ApplicationType.BLA,
                    application_number="BLA761269",
                    decision_outcome=DecisionOutcome.APPROVED,
                    indication="Treatment of Alzheimer's disease",
                    fda_page_url="https://www.fda.gov/news-events/press-announcements/fda-converts-novel-alzheimers-disease-treatment-traditional-approval"
                )
            },
            {
                "drug": Drug(
                    drug_name="Biktarvy",
                    brand_name="Biktarvy",
                    generic_name="bictegravir, emtricitabine, and tenofovir alafenamide",
                    primary_indication="Treatment of HIV-1 infection",
                    therapeutic_area="Infectious Disease",
                    route_of_administration="Oral",
                    sponsor=gilead
                ),
                "approval": Approval(
                    fda_center=FDACenter.CDER,
                    approval_date=date(2018, 2, 7),
                    application_type=ApplicationType.NDA,
                    application_number="NDA210251",
                    decision_outcome=DecisionOutcome.APPROVED,
                    indication="Treatment of HIV-1 infection in adults and pediatric patients",
                    fda_page_url="https://www.fda.gov/drugs/postmarket-drug-safety-information-patients-and-providers"
                )
            }
        ]

        # Add drugs and approvals
        for item in drugs_data:
            drug = item["drug"]
            db.add(drug)
            db.flush()  # Get drug ID

            approval = item["approval"]
            approval.drug_id = drug.id
            db.add(approval)

        db.commit()
        logger.info("✓ Created sample drugs and approvals")

        # Create some upcoming events
        today = date.today()
        future_events = [
            Event(
                drug_id=1,  # Paxlovid
                event_type=EventType.PDUFA,
                event_date=today + timedelta(days=45),
                event_status=EventStatus.SCHEDULED,
                application_number="sNDA217188-S010",
                description="PDUFA date for expanded indication",
                notes="Supplemental NDA for pediatric use expansion"
            ),
            Event(
                drug_id=3,  # Keytruda
                event_type=EventType.ADCOM,
                event_date=today + timedelta(days=30),
                event_status=EventStatus.SCHEDULED,
                application_number="sBLA125514-S099",
                description="Advisory Committee meeting for new indication",
                notes="Review of efficacy data for additional cancer type"
            ),
            Event(
                drug_id=5,  # Leqembi
                event_type=EventType.PDUFA,
                event_date=today + timedelta(days=90),
                event_status=EventStatus.SCHEDULED,
                application_number="sBLA761269-S002",
                description="PDUFA date for dosing regimen update",
                notes="Monthly dosing regimen review"
            ),
        ]

        db.add_all(future_events)
        db.commit()

        logger.info("✓ Created sample upcoming events")
        logger.info("✓ Database seeding completed successfully!")
        logger.info(f"  - {len([pfizer, moderna, jnj, merck, regeneron, biogen, gilead])} sponsors")
        logger.info(f"  - {len(drugs_data)} drugs with approvals")
        logger.info(f"  - {len(future_events)} upcoming events")

    except Exception as e:
        logger.error(f"✗ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
