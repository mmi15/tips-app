# app/services/selector.py
from __future__ import annotations

from datetime import datetime, date
from typing import List, Tuple, Optional

from sqlalchemy import select, func, exists, and_
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo

from app.db.models import Subscription, Tip, Topic, Delivery


# ----------------------------
# Utilidades de rotación diaria
# ----------------------------
def _daily_index(seed_date: date, user_id: int, topic_id: int, modulo: int) -> int:
    """
    Índice determinístico por día/usuario/topic (tu función original).
    """
    seed = int(seed_date.strftime("%Y%m%d")) ^ (
        user_id * 2654435761
    ) ^ (topic_id * 11400714819323198485 % (1 << 31))
    return abs(seed) % max(1, modulo)


# ----------------------------
# Helpers básicos de selección
# ----------------------------
def get_user_subscribed_topics(db: Session, user_id: int) -> List[Topic]:
    q = (
        select(Topic)
        .join(Subscription, Subscription.topic_id == Topic.id)
        .where(Subscription.user_id == user_id, Subscription.is_active == True, Topic.is_active == True)  # noqa: E712
        .order_by(Topic.name.asc())
    )
    return list(db.scalars(q))


def _tips_not_delivered_query(user_id: int, topic_id: int):
    """
    Subquery base: tips del topic NO entregados nunca a ese usuario.
    (Respetando tu UniqueConstraint global tip_id+user_id).
    """
    delivered_exists = (
        select(Delivery.id)
        .where(and_(Delivery.tip_id == Tip.id, Delivery.user_id == user_id))
        .limit(1)
    )
    return (
        select(Tip)
        .where(Tip.topic_id == topic_id, ~exists(delivered_exists))
    )


def _pick_many_from_query(db: Session, base_q, limit: int, strategy: str) -> List[Tip]:
    if strategy == "random":
        q = base_q.order_by(func.random()).limit(limit)
    else:
        # latest por defecto
        q = base_q.order_by(Tip.created_at.desc(), Tip.id.desc()).limit(limit)
    return list(db.scalars(q))


# ----------------------------
# API principal de selección
# ----------------------------
def pick_tip_for_topic(
    db: Session,
    user_id: int,
    topic_id: int,
    strategy: str = "latest",
    tz_name: str = "Europe/Madrid",
) -> Optional[Tip]:
    """
    Elige 1 tip NO ENTREGADO. Si no quedan, usa fallback de rotación diaria (determinístico).
    No escribe en deliveries (solo lectura). Se usará en el Paso 3.
    """
    # 1) Intento con no entregados
    base_q = _tips_not_delivered_query(user_id, topic_id)
    tip = db.scalars(
        base_q.order_by(func.random()).limit(1) if strategy == "random"
        else base_q.order_by(Tip.created_at.desc(), Tip.id.desc()).limit(1)
    ).first()
    if tip:
        return tip

    # 2) Fallback: rotación determinística sobre TODOS los tips del topic
    tz = ZoneInfo(tz_name)
    today_local = datetime.now(tz).date()
    all_q = select(Tip).where(Tip.topic_id == topic_id).order_by(
        Tip.created_at.asc(), Tip.id.asc())
    all_tips = list(db.scalars(all_q))
    if not all_tips:
        return None

    idx = _daily_index(today_local, user_id, topic_id, len(all_tips))
    return all_tips[idx]


def pick_daily_bundle(
    db: Session,
    user_id: int,
    per_topic: int = 1,
    strategy: str = "latest",
    tz_name: str = "Europe/Madrid",
    topics_override: Optional[List[Topic]] = None,   # <-- NUEVO
) -> List[Tuple[Topic, List[Tip]]]:
    """
    Devuelve (topic, [tips]) para cada topic suscrito (o para topics_override si se pasa).
    Prioriza tips NO ENTREGADOS; si se agotan, aplica fallback por rotación.
    No crea deliveries (lectura).
    """
    topics = topics_override if topics_override is not None else get_user_subscribed_topics(
        db, user_id)
    bundle: List[Tuple[Topic, List[Tip]]] = []

    for topic in topics:
        picks: List[Tip] = []

        base_q = _tips_not_delivered_query(user_id, topic.id)
        remaining = _pick_many_from_query(db, base_q, per_topic, strategy)
        picks.extend(remaining)

        if len(picks) < per_topic:
            tz = ZoneInfo(tz_name)
            today_local = datetime.now(tz).date()
            all_q = select(Tip).where(Tip.topic_id == topic.id).order_by(
                Tip.created_at.asc(), Tip.id.asc())
            all_tips = list(db.scalars(all_q))
            already_ids = {t.id for t in picks}

            if all_tips:
                start = _daily_index(today_local, user_id,
                                     topic.id, len(all_tips))
                i = 0
                while len(picks) < per_topic and i < len(all_tips):
                    t = all_tips[(start + i) % len(all_tips)]
                    if t.id not in already_ids:
                        picks.append(t)
                        already_ids.add(t.id)
                    i += 1

        if picks:
            bundle.append((topic, picks))

    return bundle


def count_remaining_by_topic(db: Session, user_id: int) -> List[Tuple[Topic, int]]:
    """
    Para cada topic suscrito, cuántos tips NO ENTREGADOS quedan.
    """
    topics = get_user_subscribed_topics(db, user_id)
    out: List[Tuple[Topic, int]] = []

    for topic in topics:
        base_q = _tips_not_delivered_query(user_id, topic.id)
        remaining = db.execute(select(func.count()).select_from(
            base_q.subquery())).scalar() or 0
        out.append((topic, int(remaining)))

    return out


# ----------------------------
# Compatibilidad con tu firma original
# ----------------------------
def get_today_tips_for_user(
    db: Session,
    user_id: int,
    tz_name: str = "Europe/Madrid",
    per_topic: int = 1,
) -> Tuple[date, List[Tip]]:
    """
    Mantiene la firma que ya usabas.
    Ahora prioriza NO ENTREGADOS y hace fallback a rotación determinística.
    """
    tz = ZoneInfo(tz_name)
    today_local = datetime.now(tz).date()

    bundle = pick_daily_bundle(
        db=db,
        user_id=user_id,
        per_topic=per_topic,
        strategy="latest",
        tz_name=tz_name,
    )

    # Aplana a la lista de tips (como hacías antes)
    flat_tips: List[Tip] = []
    for _, picks in bundle:
        flat_tips.extend(picks)

    return today_local, flat_tips
