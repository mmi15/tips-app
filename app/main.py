from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional

from app.db.session import get_db
from app.db import models
from app.schemas.topic import (
    TopicCreate, TopicRead, TopicUpdate
)
from app.schemas.subscription import (
    SubscriptionCreate, SubscriptionRead,
)

app = FastAPI(title="Tips API", version="0.2.0")


@app.get("/health")
def health_check():
    return {"status": "ok"}

# TOPICS

# LIST with optional pagination & search


@app.get("/topics", response_model=list[TopicRead])
def list_topics(
    skip: int = 0,
    limit: int = 50,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Topic)
    if q:
        # simple case-insensitive contains on name or slug
        like = f"%{q}%"
        query = query.filter(
            (models.Topic.name.ilike(like)) | (models.Topic.slug.ilike(like))
        )
    topics = query.offset(skip).limit(limit).all()
    return topics

# GET by slug (handy for frontends)


@app.get("/topics/by-slug/{slug}", response_model=TopicRead)
def get_topic_by_slug(slug: str, db: Session = Depends(get_db)):
    topic = db.query(models.Topic).filter(models.Topic.slug == slug).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found.")
    return topic


# CREATE
@app.post("/topics", response_model=TopicRead, status_code=status.HTTP_201_CREATED)
def create_topic(payload: TopicCreate, db: Session = Depends(get_db)):
    new_topic = models.Topic(name=payload.name, slug=payload.slug)
    db.add(new_topic)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Topic with this slug already exists.")
    db.refresh(new_topic)
    return new_topic

# PUT (full update)


@app.put("/topics/{topic_id}", response_model=TopicRead)
def update_topic(topic_id: int, payload: TopicUpdate, db: Session = Depends(get_db)):
    topic = db.query(models.Topic).get(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found.")

    # treat PUT as full update: require both fields present
    if payload.name is None or payload.slug is None:
        raise HTTPException(
            status_code=422, detail="Both 'name' and 'slug' are required for PUT.")

    topic.name = payload.name
    topic.slug = payload.slug
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Topic with this slug already exists.")
    db.refresh(topic)
    return topic


# PATCH (partial update)
@app.patch("/topics/{topic_id}", response_model=TopicRead)
def patch_topic(topic_id: int, payload: TopicUpdate, db: Session = Depends(get_db)):
    topic = db.query(models.Topic).get(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found.")

    if payload.name is not None:
        topic.name = payload.name
    if payload.slug is not None:
        topic.slug = payload.slug

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Topic with this slug already exists.")
    db.refresh(topic)
    return topic


# DELETE
@app.delete("/topics/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(models.Topic).get(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found.")
    db.delete(topic)
    db.commit()
    return None


# SUBSCRIPTIONS

@app.get("/users/{user_id}/subscriptions", response_model=list[SubscriptionRead])
def list_user_subscriptions(user_id: int, db: Session = Depends(get_db)):
    subs = db.query(models.Subscription).filter(
        models.Subscription.user_id == user_id).all()
    return subs


@app.post("/subscribe", response_model=SubscriptionRead, status_code=status.HTTP_201_CREATED)
def subscribe(payload: SubscriptionCreate, db: Session = Depends(get_db)):
    # Basic existence checks (optional but helpful)
    user = db.query(models.User).get(payload.user_id)
    topic = db.query(models.Topic).get(payload.topic_id)
    if not user or not topic:
        raise HTTPException(status_code=404, detail="User or Topic not found.")

    sub = models.Subscription(user_id=payload.user_id,
                              topic_id=payload.topic_id)
    db.add(sub)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Unique constraint uq_user_topic → already subscribed
        raise HTTPException(
            status_code=400, detail="User already subscribed to this topic.")
    db.refresh(sub)
    return sub


@app.delete("/unsubscribe", status_code=status.HTTP_204_NO_CONTENT)
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
