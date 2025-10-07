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


def register_deliveries_if_missing(
    db: Session,
    user_id: int,
    tips: List[Tip],
    channel: str = "app",
    status: str = "sent",
) -> int:
    """
    Inserta Delivery para cada tip si no existía (respeta UNIQUE tip_id+user_id).
    Devuelve el número de registros NUEVOS creados.
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
            # Ya existía una entrega para (tip, user); limpia y sigue
            db.rollback()
    return created


def get_delivery_history(
    db: Session,
    user_id: int,
    page: int = 1,
    size: int = 20,
    topic_id: Optional[int] = None,   # <-- NUEVO
) -> Tuple[List[dict], int]:
    """
    Devuelve el histórico de entregas del usuario, con join a tip y topic.
    Permite filtrar por topic_id si se especifica.
    Retorna: (items, total)
    """
    base_where = [Delivery.user_id == user_id]
    if topic_id is not None:
        base_where.append(Topic.id == topic_id)

    # Total (ojo: une con Tip/Topic solo si hay filtro por topic)
    total_stmt = select(func.count(Delivery.id)).join(
        Tip, Tip.id == Delivery.tip_id)
    if topic_id is not None:
        total_stmt = total_stmt.join(Topic, Topic.id == Tip.topic_id)
    total = db.execute(total_stmt.where(*base_where)).scalar_one()

    # Items enriquecidos
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


def mark_delivery_read(
    db: Session,
    user_id: int,
    delivery_id: int,
) -> dict:
    """
    Marca una Delivery del usuario como 'read' (idempotente).
    - 404 si no existe o no pertenece al usuario.
    - Devuelve el registro enriquecido (como en history) para que el cliente pueda refrescar.
    """
    # 1) Cargar delivery del usuario
    delivery = db.execute(
        select(Delivery).where(
            Delivery.id == delivery_id,
            Delivery.user_id == user_id,
        )
    ).scalar_one_or_none()

    if not delivery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found")

    # 2) Idempotencia: si ya está en 'read', no hacemos commit innecesario
    if delivery.status != "read":
        delivery.status = "read"
        db.add(delivery)
        db.commit()
        db.refresh(delivery)

    # 3) Responder enriquecido (igual estructura que history)
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
