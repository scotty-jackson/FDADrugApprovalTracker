#!/usr/bin/env python3
"""
Database initialization script.
Creates all tables in the database based on SQLAlchemy models.

Usage:
    python scripts/init_db.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.app.database import engine, init_db
from backend.app.models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Initialize the database by creating all tables."""
    try:
        logger.info("Starting database initialization...")
        init_db()
        logger.info("✓ Database tables created successfully!")
        logger.info("You can now run the seed script to populate with sample data.")
    except Exception as e:
        logger.error(f"✗ Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
