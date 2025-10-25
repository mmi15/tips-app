from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

from app.db.session import get_db
from app.db import models
from app.schemas.subscription import SubscriptionRead
from app.api.deps import get_current_active_user

# Create router for subscription-related endpoints
router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


# Request body schema for subscribe/unsubscribe actions
class SubscriptionAction(BaseModel):
    topic_id: int


# List all subscriptions for the current authenticated user
@router.get("/me", response_model=list[SubscriptionRead])
def list_my_subscriptions(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    return (
        db.query(models.Subscription)
        .filter(models.Subscription.user_id == current_user.id)
        .all()
    )


# Subscribe current user to a topic
@router.post("", response_model=SubscriptionRead, status_code=status.HTTP_201_CREATED)
def subscribe(
    payload: SubscriptionAction,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    # Find topic by ID
    topic = db.query(models.Topic).get(payload.topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found.")
    if not topic.is_active:
        raise HTTPException(status_code=400, detail="Topic is not active.")

    # Create new subscription
    sub = models.Subscription(user_id=current_user.id,
                              topic_id=payload.topic_id)
    db.add(sub)
    try:
        db.commit()  # Try to save changes
    except IntegrityError:
        db.rollback()  # Undo transaction if duplicate subscription
        raise HTTPException(status_code=400, detail="Already subscribed.")
    db.refresh(sub)  # Refresh instance with DB data
    return sub


# Unsubscribe current user from a topic
@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def unsubscribe(
    payload: SubscriptionAction,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user),
):
    # Look for existing subscription
    sub = (
        db.query(models.Subscription)
        .filter(
            models.Subscription.user_id == current_user.id,
            models.Subscription.topic_id == payload.topic_id,
        )
        .first()
    )
    if not sub:
        # Idempotent delete: return 204 even if not found
        return None

    # Delete subscription and commit changes
    db.delete(sub)
    db.commit()
    return None
