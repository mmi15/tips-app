from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional

from app.db.session import get_db
from app.db import models
from app.schemas.topic import TopicCreate, TopicUpdate, TopicRead

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("", response_model=list[TopicRead])
def list_topics(
    skip: int = 0,
    limit: int = 50,
    q: Optional[str] = None,
    only_active: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(models.Topic)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (models.Topic.name.ilike(like)) | (models.Topic.slug.ilike(like))
        )
    if only_active:
        query = query.filter(models.Topic.is_active.is_(True))
    return query.offset(skip).limit(limit).all()


@router.get("/{topic_id}", response_model=TopicRead)
def get_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(models.Topic).get(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found.")
    return topic


@router.get("/by-slug/{slug}", response_model=TopicRead)
def get_topic_by_slug(slug: str, db: Session = Depends(get_db)):
    topic = db.query(models.Topic).filter(models.Topic.slug == slug).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found.")
    return topic


@router.post("", response_model=TopicRead, status_code=status.HTTP_201_CREATED)
def create_topic(payload: TopicCreate, db: Session = Depends(get_db)):
    new_topic = models.Topic(
        name=payload.name, slug=payload.slug, is_active=payload.is_active)
    db.add(new_topic)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Topic with this slug already exists.")
    db.refresh(new_topic)
    return new_topic


@router.put("/{topic_id}", response_model=TopicRead)
def update_topic(topic_id: int, payload: TopicUpdate, db: Session = Depends(get_db)):
    topic = db.query(models.Topic).get(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found.")
    if payload.name is None or payload.slug is None or payload.is_active is None:
        raise HTTPException(
            status_code=422, detail="name, slug and is_active are required for PUT.")
    topic.name = payload.name
    topic.slug = payload.slug
    topic.is_active = payload.is_active
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Topic with this slug already exists.")
    db.refresh(topic)
    return topic


@router.patch("/{topic_id}", response_model=TopicRead)
def patch_topic(topic_id: int, payload: TopicUpdate, db: Session = Depends(get_db)):
    topic = db.query(models.Topic).get(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found.")
    if payload.name is not None:
        topic.name = payload.name
    if payload.slug is not None:
        topic.slug = payload.slug
    if payload.is_active is not None:
        topic.is_active = payload.is_active
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="Topic with this slug already exists.")
    db.refresh(topic)
    return topic


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = db.query(models.Topic).get(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found.")
    db.delete(topic)
    db.commit()
    return None
