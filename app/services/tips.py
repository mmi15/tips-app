# app/services/tips.py
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import select, func, delete
from app.db.models import Tip, Topic
from app.schemas.tip import TipCreate, TipUpdate
import hashlib


def ensure_topic_exists(db: Session, topic_id: int) -> None:
    topic = db.execute(select(Topic.id).where(
        Topic.id == topic_id)).scalar_one_or_none()
    if not topic:
        raise ValueError("Topic not found")


def make_fingerprint(topic_id: int, title: str, body: str) -> str:
    base = f"{topic_id}:{title.strip().lower()}:{body.strip()[:200]}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def create_tip(db: Session, data: TipCreate) -> Tip:
    ensure_topic_exists(db, data.topic_id)

    fp = data.fingerprint or make_fingerprint(
        data.topic_id, data.title, data.body)

    exists = db.execute(select(Tip.id).where(
        Tip.fingerprint == fp)).scalar_one_or_none()
    if exists:
        raise ValueError("Duplicated tip (fingerprint)")

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


def get_tip(db: Session, tip_id: int) -> Optional[Tip]:
    return db.execute(select(Tip).where(Tip.id == tip_id)).scalar_one_or_none()


def list_tips(
    db: Session,
    page: int = 1,
    size: int = 20,
    topic_id: Optional[int] = None,
    q: Optional[str] = None,
) -> Tuple[List[Tip], int]:
    stmt = select(Tip)
    count_stmt = select(func.count(Tip.id))

    if topic_id:
        stmt = stmt.where(Tip.topic_id == topic_id)
        count_stmt = count_stmt.where(Tip.topic_id == topic_id)

    if q:
        like = f"%{q}%"
        stmt = stmt.where((Tip.title.ilike(like)) | (Tip.body.ilike(like)))
        count_stmt = count_stmt.where(
            (Tip.title.ilike(like)) | (Tip.body.ilike(like)))

    total = db.execute(count_stmt).scalar_one()
    items = db.execute(
        stmt.order_by(Tip.created_at.desc()).offset(
            (page - 1) * size).limit(size)
    ).scalars().all()
    return items, total


def update_tip(db: Session, tip: Tip, data: TipUpdate) -> Tip:
    payload = data.model_dump(exclude_unset=True)

    if "source_url" in payload:
        payload["source_url"] = str(
            payload["source_url"]) if payload["source_url"] is not None else None

    for field, value in payload.items():
        setattr(tip, field, value)

    if "title" in payload or "body" in payload:
        tip.fingerprint = make_fingerprint(tip.topic_id, tip.title, tip.body)

    db.add(tip)
    db.commit()
    db.refresh(tip)
    return tip


def hard_delete_tip(db: Session, tip_id: int) -> None:
    db.execute(delete(Tip).where(Tip.id == tip_id))
    db.commit()
