"""
API router for email subscription management.
Allows users to subscribe to drug updates via email.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from typing import List
import logging

from app.database import get_db
from app import schemas, models
from app.email_service import email_service, generate_verification_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("/subscribe", response_model=schemas.SubscriptionStatusResponse)
async def create_subscription(
    subscription: schemas.SubscriberCreate,
    db: Session = Depends(get_db)
):
    """
    Subscribe to email notifications.
    Sends a verification email to the provided address.
    """
    try:
        # Check if subscriber already exists
        existing_subscriber = db.query(models.Subscriber).filter(
            models.Subscriber.email == subscription.email
        ).first()

        if existing_subscriber:
            if existing_subscriber.is_verified and existing_subscriber.is_active:
                return schemas.SubscriptionStatusResponse(
                    subscribed=True,
                    message="You are already subscribed!",
                    subscriber=schemas.Subscriber.model_validate(existing_subscriber)
                )
            elif not existing_subscriber.is_verified:
                # Resend verification email
                token = generate_verification_token()
                existing_subscriber.verification_token = token
                db.commit()

                await email_service.send_verification_email(subscription.email, token)

                return schemas.SubscriptionStatusResponse(
                    subscribed=False,
                    message="Verification email sent. Please check your inbox to verify your subscription.",
                    subscriber=None
                )
            else:
                # Reactivate subscription
                existing_subscriber.is_active = True
                db.commit()

                return schemas.SubscriptionStatusResponse(
                    subscribed=True,
                    message="Your subscription has been reactivated!",
                    subscriber=schemas.Subscriber.model_validate(existing_subscriber)
                )

        # Create new subscriber
        token = generate_verification_token()
        new_subscriber = models.Subscriber(
            email=subscription.email,
            verification_token=token,
            is_verified=False,
            is_active=True
        )

        db.add(new_subscriber)
        db.commit()
        db.refresh(new_subscriber)

        # Send verification email
        await email_service.send_verification_email(subscription.email, token)

        logger.info(f"New subscription created: {subscription.email}")

        return schemas.SubscriptionStatusResponse(
            subscribed=False,
            message="Verification email sent. Please check your inbox to verify your subscription.",
            subscriber=None
        )

    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create subscription")


@router.get("/verify", response_model=schemas.VerifyEmailResponse)
def verify_email(
    token: str = Query(..., description="Verification token from email"),
    db: Session = Depends(get_db)
):
    """
    Verify email address using token sent via email.
    """
    try:
        subscriber = db.query(models.Subscriber).filter(
            models.Subscriber.verification_token == token
        ).first()

        if not subscriber:
            raise HTTPException(status_code=404, detail="Invalid verification token")

        if subscriber.is_verified:
            return schemas.VerifyEmailResponse(
                success=True,
                message="Email already verified"
            )

        # Mark as verified
        subscriber.is_verified = True
        subscriber.verification_token = None  # Clear token after use
        db.commit()

        logger.info(f"Email verified: {subscriber.email}")

        return schemas.VerifyEmailResponse(
            success=True,
            message="Email successfully verified! You will now receive notifications for your subscribed drugs."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying email: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to verify email")


@router.post("/drugs/{drug_id}", response_model=dict)
def subscribe_to_drug(
    drug_id: int,
    email: str = Query(..., description="Subscriber email address"),
    db: Session = Depends(get_db)
):
    """
    Subscribe to updates for a specific drug.
    User must have a verified email subscription first.
    """
    try:
        # Check if drug exists
        drug = db.query(models.Drug).filter(models.Drug.id == drug_id).first()
        if not drug:
            raise HTTPException(status_code=404, detail="Drug not found")

        # Check if subscriber exists and is verified
        subscriber = db.query(models.Subscriber).filter(
            models.Subscriber.email == email
        ).first()

        if not subscriber:
            raise HTTPException(
                status_code=404,
                detail="Email not found. Please subscribe first at /subscriptions/subscribe"
            )

        if not subscriber.is_verified:
            raise HTTPException(
                status_code=400,
                detail="Please verify your email before subscribing to drugs"
            )

        if not subscriber.is_active:
            raise HTTPException(
                status_code=400,
                detail="Your subscription is inactive. Please reactivate it first."
            )

        # Check if already subscribed to this drug
        existing = db.query(models.DrugSubscription).filter(
            and_(
                models.DrugSubscription.subscriber_id == subscriber.id,
                models.DrugSubscription.drug_id == drug_id
            )
        ).first()

        if existing:
            return {
                "success": True,
                "message": f"Already subscribed to {drug.brand_name or drug.drug_name}"
            }

        # Create subscription
        drug_subscription = models.DrugSubscription(
            subscriber_id=subscriber.id,
            drug_id=drug_id
        )

        db.add(drug_subscription)
        db.commit()

        logger.info(f"Drug subscription created: {email} -> {drug.drug_name}")

        return {
            "success": True,
            "message": f"Successfully subscribed to {drug.brand_name or drug.drug_name}. You will receive email notifications for new approvals and events."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error subscribing to drug: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to subscribe to drug")


@router.delete("/drugs/{drug_id}", response_model=dict)
def unsubscribe_from_drug(
    drug_id: int,
    email: str = Query(..., description="Subscriber email address"),
    db: Session = Depends(get_db)
):
    """
    Unsubscribe from updates for a specific drug.
    """
    try:
        # Get subscriber
        subscriber = db.query(models.Subscriber).filter(
            models.Subscriber.email == email
        ).first()

        if not subscriber:
            raise HTTPException(status_code=404, detail="Subscriber not found")

        # Find and delete subscription
        drug_subscription = db.query(models.DrugSubscription).filter(
            and_(
                models.DrugSubscription.subscriber_id == subscriber.id,
                models.DrugSubscription.drug_id == drug_id
            )
        ).first()

        if not drug_subscription:
            raise HTTPException(status_code=404, detail="Not subscribed to this drug")

        db.delete(drug_subscription)
        db.commit()

        logger.info(f"Drug unsubscription: {email} -> drug {drug_id}")

        return {
            "success": True,
            "message": "Successfully unsubscribed from drug"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsubscribing from drug: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to unsubscribe")


@router.get("/my-subscriptions", response_model=List[schemas.DrugSubscriptionResponse])
def get_my_subscriptions(
    email: str = Query(..., description="Subscriber email address"),
    db: Session = Depends(get_db)
):
    """
    Get list of drugs the user is subscribed to.
    """
    try:
        subscriber = db.query(models.Subscriber).filter(
            models.Subscriber.email == email
        ).first()

        if not subscriber:
            raise HTTPException(status_code=404, detail="Subscriber not found")

        # Get all subscriptions with drug info
        subscriptions = db.query(models.DrugSubscription).options(
            joinedload(models.DrugSubscription.drug)
        ).filter(
            models.DrugSubscription.subscriber_id == subscriber.id
        ).all()

        result = []
        for sub in subscriptions:
            result.append(schemas.DrugSubscriptionResponse(
                id=sub.id,
                drug_id=sub.drug_id,
                drug_name=sub.drug.brand_name or sub.drug.drug_name,
                created_at=sub.created_at
            ))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subscriptions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get subscriptions")


@router.get("/preferences", response_model=schemas.Subscriber)
def get_preferences(
    email: str = Query(..., description="Subscriber email address"),
    db: Session = Depends(get_db)
):
    """
    Get subscriber preferences.
    """
    try:
        subscriber = db.query(models.Subscriber).filter(
            models.Subscriber.email == email
        ).first()

        if not subscriber:
            raise HTTPException(status_code=404, detail="Subscriber not found")

        return schemas.Subscriber.model_validate(subscriber)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to get preferences")


@router.patch("/preferences", response_model=schemas.Subscriber)
def update_preferences(
    updates: schemas.SubscriberUpdate,
    email: str = Query(..., description="Subscriber email address"),
    db: Session = Depends(get_db)
):
    """
    Update subscriber notification preferences.
    """
    try:
        subscriber = db.query(models.Subscriber).filter(
            models.Subscriber.email == email
        ).first()

        if not subscriber:
            raise HTTPException(status_code=404, detail="Subscriber not found")

        # Update only provided fields
        update_data = updates.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(subscriber, field, value)

        db.commit()
        db.refresh(subscriber)

        logger.info(f"Preferences updated: {email}")

        return schemas.Subscriber.model_validate(subscriber)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update preferences")


@router.post("/unsubscribe-all", response_model=dict)
def unsubscribe_all(
    email: str = Query(..., description="Subscriber email address"),
    db: Session = Depends(get_db)
):
    """
    Unsubscribe from all notifications.
    Sets subscriber to inactive but preserves account for potential reactivation.
    """
    try:
        subscriber = db.query(models.Subscriber).filter(
            models.Subscriber.email == email
        ).first()

        if not subscriber:
            raise HTTPException(status_code=404, detail="Subscriber not found")

        subscriber.is_active = False
        db.commit()

        logger.info(f"Full unsubscribe: {email}")

        return {
            "success": True,
            "message": "Successfully unsubscribed from all notifications"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsubscribing: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to unsubscribe")


@router.get("/check/{drug_id}", response_model=dict)
def check_subscription_status(
    drug_id: int,
    email: str = Query(..., description="Subscriber email address"),
    db: Session = Depends(get_db)
):
    """
    Check if user is subscribed to a specific drug.
    """
    try:
        subscriber = db.query(models.Subscriber).filter(
            models.Subscriber.email == email
        ).first()

        if not subscriber or not subscriber.is_verified or not subscriber.is_active:
            return {"subscribed": False}

        # Check drug subscription
        drug_sub = db.query(models.DrugSubscription).filter(
            and_(
                models.DrugSubscription.subscriber_id == subscriber.id,
                models.DrugSubscription.drug_id == drug_id
            )
        ).first()

        return {
            "subscribed": drug_sub is not None,
            "verified": subscriber.is_verified,
            "active": subscriber.is_active
        }

    except Exception as e:
        logger.error(f"Error checking subscription status: {e}")
        return {"subscribed": False}
