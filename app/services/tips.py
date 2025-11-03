# app/services/tips.py

from typing import Optional, Tuple, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func, delete
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from app.db.models import Tip, Topic, Delivery
from app.schemas.tip import TipCreate, TipUpdate
import hashlib

# ==============================
# Tip Service Layer
# ==============================
# This module contains business logic for managing tips and deliveries.
# It handles creation, updates, deletion, deduplication, and user delivery tracking.

# ------------------------------
# Validate topic existence
# ------------------------------


def ensure_topic_exists(db: Session, topic_id: int) -> None:
    """Ensure that a topic with the given ID exists, otherwise raise ValueError."""
    topic = db.execute(select(Topic.id).where(
        Topic.id == topic_id)).scalar_one_or_none()
    if not topic:
        raise ValueError("Topic not found")


# ------------------------------
# Generate unique fingerprint for deduplication
# ------------------------------
def make_fingerprint(topic_id: int, title: str, body: str) -> str:
    """
    Generate a unique SHA-256 hash combining topic_id, title, and the first 200 characters of the body.
    This helps prevent storing duplicate tips with the same content.
    """
    base = f"{topic_id}:{title.strip().lower()}:{body.strip()[:200]}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


# ------------------------------
# Create new tip
# ------------------------------
def create_tip(db: Session, data: TipCreate) -> Tip:
    """Create a new tip, ensuring its topic exists and avoiding duplicates via fingerprint."""
    ensure_topic_exists(db, data.topic_id)

    # Use provided fingerprint or generate one automatically
    fp = data.fingerprint or make_fingerprint(
        data.topic_id, data.title, data.body)

    # Check for duplicates
    exists = db.execute(select(Tip.id).where(
        Tip.fingerprint == fp)).scalar_one_or_none()
    if exists:
        raise ValueError("Duplicated tip (fingerprint)")

    # Create and persist new tip
    tip = Tip(
        topic_id=data.topic_id,
        title=data.title,
        body=data.body,
        source_url=str(data.source_url) if data.source_url else None,
        fingerprint=fp,
    )
    db.add(tip)
    db.commit()
    db.refresh(tip)
    return tip


# ------------------------------
# Retrieve a tip by ID
# ------------------------------
def get_tip(db: Session, tip_id: int) -> Optional[Tip]:
    """Return a Tip object by its ID, or None if not found."""
    return db.execute(select(Tip).where(Tip.id == tip_id)).scalar_one_or_none()


# ------------------------------
# List tips with pagination and filtering
# ------------------------------
def list_tips(
    db: Session,
    page: int = 1,
    size: int = 20,
    topic_id: Optional[int] = None,
    q: Optional[str] = None,
) -> Tuple[List[Tip], int]:
    """
    List tips with optional filtering by topic_id and keyword (title/body).
    Returns a tuple: (items, total_count).
    """
    stmt = select(Tip)
    count_stmt = select(func.count(Tip.id))

    # Optional filtering by topic
    if topic_id:
        stmt = stmt.where(Tip.topic_id == topic_id)
        count_stmt = count_stmt.where(Tip.topic_id == topic_id)

    # Optional search query (case-insensitive)
    if q:
        like = f"%{q}%"
        stmt = stmt.where((Tip.title.ilike(like)) | (Tip.body.ilike(like)))
        count_stmt = count_stmt.where(
            (Tip.title.ilike(like)) | (Tip.body.ilike(like)))

    total = db.execute(count_stmt).scalar_one()
    items = (
        db.execute(
            stmt.order_by(Tip.created_at.desc()).offset(
                (page - 1) * size).limit(size)
        )
        .scalars()
        .all()
    )
    return items, total


# ------------------------------
# Update existing tip
# ------------------------------
def update_tip(db: Session, tip: Tip, data: TipUpdate) -> Tip:
    """
    Update a tip with the provided data.
    Recalculates fingerprint if title/body changed.
    """
    payload = data.model_dump(exclude_unset=True)

    # Normalize source_url
    if "source_url" in payload:
        payload["source_url"] = (
            str(payload["source_url"]
                ) if payload["source_url"] is not None else None
        )

    # Apply field changes
    for field, value in payload.items():
        setattr(tip, field, value)

    # Recompute fingerprint if content changed
    if "title" in payload or "body" in payload:
        tip.fingerprint = make_fingerprint(tip.topic_id, tip.title, tip.body)

    db.add(tip)
    db.commit()
    db.refresh(tip)
    return tip


# ------------------------------
# Permanently delete a tip
# ------------------------------
def hard_delete_tip(db: Session, tip_id: int) -> None:
    """Permanently delete a tip from the database."""
    db.execute(delete(Tip).where(Tip.id == tip_id))
    db.commit()


# ------------------------------
# Register deliveries if missing
# ------------------------------
def register_deliveries_if_missing(
    db: Session,
    user_id: int,
    tips: List[Tip],
    channel: str = "app",
    status: str = "sent",
) -> int:
    """
    Insert a Delivery record for each tip if one doesn't already exist.
    Enforces UNIQUE(tip_id, user_id).
    Returns the number of new deliveries created.
    """
    created = 0
    for tip in tips:
        try:
            d = Delivery(
                tip_id=tip.id,
                user_id=user_id,
                delivered_at=datetime.utcnow(),
                channel=channel,
                status=status,
            )
            db.add(d)
            db.commit()
            created += 1
        except IntegrityError:
            # Delivery already exists for this (tip, user); skip
            db.rollback()
    return created


# ------------------------------
# Get delivery history for a user
# ------------------------------
def get_delivery_history(
    db: Session,
    user_id: int,
    page: int = 1,
    size: int = 20,
    topic_id: Optional[int] = None,
) -> Tuple[List[dict], int]:
    """
    Retrieve a paginated list of deliveries for a given user, joined with tip and topic data.
    Can filter by topic_id.
    Returns a tuple: (items, total_count).
    """
    base_where = [Delivery.user_id == user_id]
    if topic_id is not None:
        base_where.append(Topic.id == topic_id)

    # Count total results (join Topic only when filtering)
    total_stmt = select(func.count(Delivery.id)).join(
        Tip, Tip.id == Delivery.tip_id)
    if topic_id is not None:
        total_stmt = total_stmt.join(Topic, Topic.id == Tip.topic_id)
    total = db.execute(total_stmt.where(*base_where)).scalar_one()

    # Retrieve delivery list (joined data)
    stmt = (
        select(
            Delivery.id.label("delivery_id"),
            Delivery.delivered_at,
            Delivery.channel,
            Delivery.status,
            Tip.id.label("tip_id"),
            Tip.title,
            Tip.body,
            Tip.source_url,
            Tip.created_at.label("tip_created_at"),
            Topic.id.label("topic_id"),
            Topic.name.label("topic_name"),
            Topic.slug.label("topic_slug"),
        )
        .join(Tip, Tip.id == Delivery.tip_id)
        .join(Topic, Topic.id == Tip.topic_id)
        .where(*base_where)
        .order_by(Delivery.delivered_at.desc(), Delivery.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )

    rows = db.execute(stmt).all()

    # Build enriched response objects
    items = [
        {
            "delivery_id": r.delivery_id,
            "delivered_at": r.delivered_at,
            "channel": r.channel,
            "status": r.status,
            "tip": {
                "id": r.tip_id,
                "title": r.title,
                "body": r.body,
                "source_url": r.source_url,
                "created_at": r.tip_created_at,
            },
            "topic": {
                "id": r.topic_id,
                "name": r.topic_name,
                "slug": r.topic_slug,
            },
        }
        for r in rows
    ]
    return items, total


# ------------------------------
# Mark delivery as read (idempotent)
# ------------------------------
def mark_delivery_read(
    db: Session,
    user_id: int,
    delivery_id: int,
) -> dict:
    """
    Mark a delivery as 'read' for a user.
    - Returns 404 if not found or not owned by the user.
    - Idempotent: repeated calls do not change the result.
    - Returns the same enriched structure as in the history response.
    """
    # 1) Retrieve the delivery belonging to the user
    delivery = db.execute(
        select(Delivery).where(
            Delivery.id == delivery_id,
            Delivery.user_id == user_id,
        )
    ).scalar_one_or_none()

    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found"
        )

    # 2) Update only if status is not already 'read'
    if delivery.status != "read":
        delivery.status = "read"
        db.add(delivery)
        db.commit()
        db.refresh(delivery)

    # 3) Return enriched delivery info (joined with tip & topic)
    row = db.execute(
        select(
            Delivery.id.label("delivery_id"),
            Delivery.delivered_at,
            Delivery.channel,
            Delivery.status,
            Tip.id.label("tip_id"),
            Tip.title,
            Tip.body,
            Tip.source_url,
            Tip.created_at.label("tip_created_at"),
            Topic.id.label("topic_id"),
            Topic.name.label("topic_name"),
            Topic.slug.label("topic_slug"),
        )
        .join(Tip, Tip.id == Delivery.tip_id)
        .join(Topic, Topic.id == Tip.topic_id)
        .where(Delivery.id == delivery_id)
    ).one()

    return {
        "delivery_id": row.delivery_id,
        "delivered_at": row.delivered_at,
        "channel": row.channel,
        "status": row.status,
        "tip": {
            "id": row.tip_id,
            "title": row.title,
            "body": row.body,
            "source_url": row.source_url,
            "created_at": row.tip_created_at,
        },
        "topic": {
            "id": row.topic_id,
            "name": row.topic_name,
            "slug": row.topic_slug,
        },
    }
