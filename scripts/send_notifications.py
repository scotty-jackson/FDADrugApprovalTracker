#!/usr/bin/env python3
"""
Background job to send email notifications to subscribers.

This script checks for:
1. New approvals for subscribed drugs
2. New events for subscribed drugs
3. Upcoming event reminders (X days before)

Designed to run periodically via cron (e.g., hourly or daily).

Usage:
    python scripts/send_notifications.py [--dry-run]
"""
import sys
import os
import argparse
import asyncio
from datetime import datetime, timedelta, date
from sqlalchemy import and_

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.app.database import SessionLocal
from backend.app.models import (
    Subscriber, DrugSubscription, Approval, Event,
    NotificationLog, NotificationType, EventStatus
)
from backend.app.email_service import email_service
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NotificationSender:
    """
    Handles sending email notifications to subscribers.
    """

    def __init__(self, db_session, dry_run=False):
        self.db = db_session
        self.dry_run = dry_run
        self.notifications_sent = 0

    async def send_new_approval_notifications(self):
        """
        Notify subscribers about new approvals for their tracked drugs.
        Only sends for approvals created in the last 24 hours.
        """
        logger.info("Checking for new approvals...")

        # Get approvals from last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)

        new_approvals = self.db.query(Approval).filter(
            Approval.created_at >= yesterday
        ).all()

        logger.info(f"Found {len(new_approvals)} new approvals")

        for approval in new_approvals:
            # Get subscribers for this drug
            subscriptions = self.db.query(DrugSubscription).join(Subscriber).filter(
                and_(
                    DrugSubscription.drug_id == approval.drug_id,
                    Subscriber.is_active == True,
                    Subscriber.is_verified == True,
                    Subscriber.notify_new_approvals == True
                )
            ).all()

            for subscription in subscriptions:
                subscriber = subscription.subscriber

                # Check if already notified about this approval
                existing_notification = self.db.query(NotificationLog).filter(
                    and_(
                        NotificationLog.subscriber_id == subscriber.id,
                        NotificationLog.approval_id == approval.id,
                        NotificationLog.notification_type == NotificationType.NEW_APPROVAL
                    )
                ).first()

                if existing_notification:
                    continue  # Already notified

                # Send notification
                try:
                    drug = approval.drug
                    drug_name = drug.brand_name or drug.drug_name

                    if not self.dry_run:
                        success = await email_service.send_new_approval_notification(
                            email=subscriber.email,
                            drug_name=drug_name,
                            approval_date=approval.approval_date.strftime("%B %d, %Y") if approval.approval_date else "N/A",
                            indication=approval.indication or drug.primary_indication or "N/A",
                            drug_id=drug.id
                        )

                        # Log notification
                        notification_log = NotificationLog(
                            subscriber_id=subscriber.id,
                            drug_id=drug.id,
                            approval_id=approval.id,
                            notification_type=NotificationType.NEW_APPROVAL,
                            subject=f"New FDA Approval: {drug_name}",
                            email_sent_successfully=success
                        )
                        self.db.add(notification_log)
                        self.db.commit()

                        if success:
                            self.notifications_sent += 1
                            logger.info(f"Sent new approval notification to {subscriber.email} for {drug_name}")
                        else:
                            logger.error(f"Failed to send notification to {subscriber.email}")
                    else:
                        logger.info(f"[DRY RUN] Would send new approval notification to {subscriber.email} for {drug_name}")
                        self.notifications_sent += 1

                except Exception as e:
                    logger.error(f"Error sending notification: {e}")

    async def send_new_event_notifications(self):
        """
        Notify subscribers about new events for their tracked drugs.
        Only sends for events created in the last 24 hours.
        """
        logger.info("Checking for new events...")

        yesterday = datetime.utcnow() - timedelta(days=1)

        new_events = self.db.query(Event).filter(
            and_(
                Event.created_at >= yesterday,
                Event.drug_id.isnot(None)
            )
        ).all()

        logger.info(f"Found {len(new_events)} new events")

        for event in new_events:
            # Get subscribers for this drug
            subscriptions = self.db.query(DrugSubscription).join(Subscriber).filter(
                and_(
                    DrugSubscription.drug_id == event.drug_id,
                    Subscriber.is_active == True,
                    Subscriber.is_verified == True,
                    Subscriber.notify_new_events == True
                )
            ).all()

            for subscription in subscriptions:
                subscriber = subscription.subscriber

                # Check if already notified
                existing_notification = self.db.query(NotificationLog).filter(
                    and_(
                        NotificationLog.subscriber_id == subscriber.id,
                        NotificationLog.event_id == event.id,
                        NotificationLog.notification_type == NotificationType.NEW_EVENT
                    )
                ).first()

                if existing_notification:
                    continue

                # Send notification
                try:
                    drug = event.drug
                    drug_name = drug.brand_name or drug.drug_name

                    if not self.dry_run:
                        success = await email_service.send_new_event_notification(
                            email=subscriber.email,
                            drug_name=drug_name,
                            event_type=event.event_type.value,
                            event_date=event.event_date.strftime("%B %d, %Y") if event.event_date else "TBD",
                            description=event.description or "No description available",
                            drug_id=drug.id
                        )

                        # Log notification
                        notification_log = NotificationLog(
                            subscriber_id=subscriber.id,
                            drug_id=drug.id,
                            event_id=event.id,
                            notification_type=NotificationType.NEW_EVENT,
                            subject=f"New {event.event_type.value} Scheduled: {drug_name}",
                            email_sent_successfully=success
                        )
                        self.db.add(notification_log)
                        self.db.commit()

                        if success:
                            self.notifications_sent += 1
                            logger.info(f"Sent new event notification to {subscriber.email} for {drug_name}")
                        else:
                            logger.error(f"Failed to send notification to {subscriber.email}")
                    else:
                        logger.info(f"[DRY RUN] Would send new event notification to {subscriber.email} for {drug_name}")
                        self.notifications_sent += 1

                except Exception as e:
                    logger.error(f"Error sending notification: {e}")

    async def send_event_reminders(self):
        """
        Send reminders for upcoming events based on subscriber preferences.
        """
        logger.info("Checking for upcoming event reminders...")

        # Get all active subscribers with reminder preferences
        subscribers = self.db.query(Subscriber).filter(
            and_(
                Subscriber.is_active == True,
                Subscriber.is_verified == True,
                Subscriber.notify_event_reminders == True
            )
        ).all()

        logger.info(f"Found {len(subscribers)} subscribers with event reminders enabled")

        for subscriber in subscribers:
            reminder_days = subscriber.reminder_days_before
            target_date = date.today() + timedelta(days=reminder_days)

            # Get subscribed drugs
            drug_ids = [sub.drug_id for sub in subscriber.subscriptions]

            if not drug_ids:
                continue

            # Find upcoming events for subscribed drugs
            upcoming_events = self.db.query(Event).filter(
                and_(
                    Event.drug_id.in_(drug_ids),
                    Event.event_date == target_date,
                    Event.event_status == EventStatus.SCHEDULED
                )
            ).all()

            for event in upcoming_events:
                # Check if already sent reminder
                existing_notification = self.db.query(NotificationLog).filter(
                    and_(
                        NotificationLog.subscriber_id == subscriber.id,
                        NotificationLog.event_id == event.id,
                        NotificationLog.notification_type == NotificationType.EVENT_REMINDER
                    )
                ).first()

                if existing_notification:
                    continue

                # Send reminder
                try:
                    drug = event.drug
                    drug_name = drug.brand_name or drug.drug_name

                    if not self.dry_run:
                        success = await email_service.send_event_reminder(
                            email=subscriber.email,
                            drug_name=drug_name,
                            event_type=event.event_type.value,
                            event_date=event.event_date.strftime("%B %d, %Y"),
                            days_until=reminder_days,
                            drug_id=drug.id
                        )

                        # Log notification
                        notification_log = NotificationLog(
                            subscriber_id=subscriber.id,
                            drug_id=drug.id,
                            event_id=event.id,
                            notification_type=NotificationType.EVENT_REMINDER,
                            subject=f"Reminder: {event.event_type.value} for {drug_name} in {reminder_days} days",
                            email_sent_successfully=success
                        )
                        self.db.add(notification_log)
                        self.db.commit()

                        if success:
                            self.notifications_sent += 1
                            logger.info(f"Sent event reminder to {subscriber.email} for {drug_name}")
                        else:
                            logger.error(f"Failed to send reminder to {subscriber.email}")
                    else:
                        logger.info(f"[DRY RUN] Would send event reminder to {subscriber.email} for {drug_name}")
                        self.notifications_sent += 1

                except Exception as e:
                    logger.error(f"Error sending reminder: {e}")


async def main():
    """Main entry point for notification sending."""
    parser = argparse.ArgumentParser(description='Send email notifications to subscribers')
    parser.add_argument('--dry-run', action='store_true',
                        help='Run without actually sending emails')
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Email Notification Job Started")
    if args.dry_run:
        logger.info("DRY RUN MODE - No emails will be sent")
    logger.info("=" * 60)

    db = SessionLocal()

    try:
        sender = NotificationSender(db, dry_run=args.dry_run)

        # Send all types of notifications
        await sender.send_new_approval_notifications()
        await sender.send_new_event_notifications()
        await sender.send_event_reminders()

        logger.info("=" * 60)
        logger.info(f"✓ Notification job completed successfully")
        logger.info(f"  Total notifications sent: {sender.notifications_sent}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"✗ Fatal error during notification job: {e}", exc_info=True)
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
