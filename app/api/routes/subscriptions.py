from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.db import models
from app.schemas.subscription import SubscriptionCreate, SubscriptionRead

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/users/{user_id}", response_model=list[SubscriptionRead])
def list_user_subscriptions(user_id: int, db: Session = Depends(get_db)):
    subs = db.query(models.Subscription).filter(
        models.Subscription.user_id == user_id).all()
    return subs


@router.get("/topics/{topic_id}", response_model=list[SubscriptionRead])
def list_topic_subscriptions(topic_id: int, db: Session = Depends(get_db)):
    subs = db.query(models.Subscription).filter(
        models.Subscription.topic_id == topic_id).all()
    return subs


@router.post("", response_model=SubscriptionRead, status_code=status.HTTP_201_CREATED)
def subscribe(payload: SubscriptionCreate, db: Session = Depends(get_db)):
    # Optional existence checks (helpful error messages)
    user = db.query(models.User).get(payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    topic = db.query(models.Topic).get(payload.topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found.")

    sub = models.Subscription(user_id=payload.user_id,
                              topic_id=payload.topic_id)
    db.add(sub)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # UNIQUE (user_id, topic_id)
        raise HTTPException(
            status_code=400, detail="User already subscribed to this topic.")
    db.refresh(sub)
    return sub


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def unsubscribe(payload: SubscriptionCreate, db: Session = Depends(get_db)):
    sub = (
        db.query(models.Subscription)
        .filter(
            models.Subscription.user_id == payload.user_id,
            models.Subscription.topic_id == payload.topic_id,
        )
        .first()
    )
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found.")
    db.delete(sub)
    db.commit()
    return None
