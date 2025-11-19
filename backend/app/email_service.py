"""
Email service for sending notifications to subscribers.
Supports both SMTP and console output for development.
"""
import logging
import secrets
from typing import List, Optional
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
from jinja2 import Template

from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending email notifications.
    """

    def __init__(self):
        self.smtp_host = getattr(settings, 'smtp_host', 'localhost')
        self.smtp_port = getattr(settings, 'smtp_port', 1025)
        self.smtp_username = getattr(settings, 'smtp_username', '')
        self.smtp_password = getattr(settings, 'smtp_password', '')
        self.smtp_use_tls = getattr(settings, 'smtp_use_tls', False)
        self.from_email = getattr(settings, 'from_email', 'noreply@fdatracker.com')
        self.from_name = getattr(settings, 'from_name', 'FDA Drug Approval Tracker')
        self.base_url = getattr(settings, 'base_url', 'http://localhost:5173')

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email to a recipient.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body (optional)

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = f"{self.from_name} <{self.from_email}>"
            message['To'] = to_email

            # Add text content
            if text_content:
                part1 = MIMEText(text_content, 'plain')
                message.attach(part1)

            # Add HTML content
            part2 = MIMEText(html_content, 'html')
            message.attach(part2)

            # Send email
            if self.smtp_host == 'console':
                # Console mode for development
                logger.info("=" * 60)
                logger.info(f"EMAIL TO: {to_email}")
                logger.info(f"SUBJECT: {subject}")
                logger.info("=" * 60)
                logger.info(html_content)
                logger.info("=" * 60)
                return True
            else:
                # Send via SMTP
                await aiosmtplib.send(
                    message,
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.smtp_username if self.smtp_username else None,
                    password=self.smtp_password if self.smtp_password else None,
                    use_tls=self.smtp_use_tls,
                )
                logger.info(f"Email sent successfully to {to_email}")
                return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False

    async def send_verification_email(self, email: str, token: str) -> bool:
        """
        Send email verification link to new subscriber.
        """
        verify_url = f"{self.base_url}/verify?token={token}"

        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1976d2; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f5f5f5; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #1976d2; color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Verify Your Email</h1>
                </div>
                <div class="content">
                    <p>Thank you for subscribing to FDA Drug Approval Tracker!</p>
                    <p>Please click the button below to verify your email address and activate your subscription:</p>
                    <p style="text-align: center;">
                        <a href="{verify_url}" class="button">Verify Email Address</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all;">{verify_url}</p>
                    <p>This link will expire in 24 hours.</p>
                </div>
                <div class="footer">
                    <p>If you didn't request this subscription, you can safely ignore this email.</p>
                    <p>&copy; {year} FDA Drug Approval Tracker</p>
                </div>
            </div>
        </body>
        </html>
        """

        html_content = html_template.format(
            verify_url=verify_url,
            year=datetime.utcnow().year
        )

        text_content = f"""
        Verify Your Email

        Thank you for subscribing to FDA Drug Approval Tracker!

        Please visit the following link to verify your email address:
        {verify_url}

        This link will expire in 24 hours.

        If you didn't request this subscription, you can safely ignore this email.
        """

        return await self.send_email(
            to_email=email,
            subject="Verify your FDA Drug Tracker subscription",
            html_content=html_content,
            text_content=text_content
        )

    async def send_new_approval_notification(
        self,
        email: str,
        drug_name: str,
        approval_date: str,
        indication: str,
        drug_id: int
    ) -> bool:
        """
        Notify subscriber about a new approval for a drug they're tracking.
        """
        drug_url = f"{self.base_url}/drugs/{drug_id}"

        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1976d2; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f5f5f5; }}
                .drug-info {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #1976d2; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #1976d2; color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>New FDA Approval</h1>
                </div>
                <div class="content">
                    <p>Great news! The FDA has approved <strong>{drug_name}</strong>.</p>
                    <div class="drug-info">
                        <h3>{drug_name}</h3>
                        <p><strong>Approval Date:</strong> {approval_date}</p>
                        <p><strong>Indication:</strong> {indication}</p>
                    </div>
                    <p style="text-align: center;">
                        <a href="{drug_url}" class="button">View Full Details</a>
                    </p>
                </div>
                <div class="footer">
                    <p>You're receiving this because you subscribed to updates for {drug_name}.</p>
                    <p><a href="{base_url}/unsubscribe">Manage your subscriptions</a></p>
                    <p>&copy; {year} FDA Drug Approval Tracker</p>
                </div>
            </div>
        </body>
        </html>
        """

        html_content = html_template.format(
            drug_name=drug_name,
            approval_date=approval_date,
            indication=indication,
            drug_url=drug_url,
            base_url=self.base_url,
            year=datetime.utcnow().year
        )

        return await self.send_email(
            to_email=email,
            subject=f"New FDA Approval: {drug_name}",
            html_content=html_content
        )

    async def send_new_event_notification(
        self,
        email: str,
        drug_name: str,
        event_type: str,
        event_date: str,
        description: str,
        drug_id: int
    ) -> bool:
        """
        Notify subscriber about a new event for a drug they're tracking.
        """
        drug_url = f"{self.base_url}/drugs/{drug_id}"

        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1976d2; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f5f5f5; }}
                .event-info {{ background-color: white; padding: 15px; margin: 15px 0; border-left: 4px solid #dc004e; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #1976d2; color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>New FDA Event Scheduled</h1>
                </div>
                <div class="content">
                    <p>A new {event_type} event has been scheduled for <strong>{drug_name}</strong>.</p>
                    <div class="event-info">
                        <h3>{drug_name}</h3>
                        <p><strong>Event Type:</strong> {event_type}</p>
                        <p><strong>Event Date:</strong> {event_date}</p>
                        <p><strong>Description:</strong> {description}</p>
                    </div>
                    <p style="text-align: center;">
                        <a href="{drug_url}" class="button">View Full Details</a>
                    </p>
                </div>
                <div class="footer">
                    <p>You're receiving this because you subscribed to updates for {drug_name}.</p>
                    <p><a href="{base_url}/unsubscribe">Manage your subscriptions</a></p>
                    <p>&copy; {year} FDA Drug Approval Tracker</p>
                </div>
            </div>
        </body>
        </html>
        """

        html_content = html_template.format(
            drug_name=drug_name,
            event_type=event_type,
            event_date=event_date,
            description=description,
            drug_url=drug_url,
            base_url=self.base_url,
            year=datetime.utcnow().year
        )

        return await self.send_email(
            to_email=email,
            subject=f"{event_type} Scheduled: {drug_name}",
            html_content=html_content
        )

    async def send_event_reminder(
        self,
        email: str,
        drug_name: str,
        event_type: str,
        event_date: str,
        days_until: int,
        drug_id: int
    ) -> bool:
        """
        Send reminder for upcoming event.
        """
        drug_url = f"{self.base_url}/drugs/{drug_id}"

        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #ff9800; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f5f5f5; }}
                .reminder {{ background-color: #fff3e0; padding: 15px; margin: 15px 0; border-left: 4px solid #ff9800; }}
                .button {{ display: inline-block; padding: 12px 24px; background-color: #1976d2; color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
                .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⏰ Event Reminder</h1>
                </div>
                <div class="content">
                    <p>Reminder: An FDA event for <strong>{drug_name}</strong> is coming up in {days_until} days.</p>
                    <div class="reminder">
                        <h3>{drug_name}</h3>
                        <p><strong>Event Type:</strong> {event_type}</p>
                        <p><strong>Event Date:</strong> {event_date}</p>
                        <p><strong>Days Until Event:</strong> {days_until}</p>
                    </div>
                    <p style="text-align: center;">
                        <a href="{drug_url}" class="button">View Full Details</a>
                    </p>
                </div>
                <div class="footer">
                    <p>You're receiving this because you subscribed to updates for {drug_name}.</p>
                    <p><a href="{base_url}/unsubscribe">Manage your subscriptions</a></p>
                    <p>&copy; {year} FDA Drug Approval Tracker</p>
                </div>
            </div>
        </body>
        </html>
        """

        html_content = html_template.format(
            drug_name=drug_name,
            event_type=event_type,
            event_date=event_date,
            days_until=days_until,
            drug_url=drug_url,
            base_url=self.base_url,
            year=datetime.utcnow().year
        )

        return await self.send_email(
            to_email=email,
            subject=f"Reminder: {event_type} for {drug_name} in {days_until} days",
            html_content=html_content
        )


def generate_verification_token() -> str:
    """Generate a secure random token for email verification."""
    return secrets.token_urlsafe(32)


# Global email service instance
email_service = EmailService()
