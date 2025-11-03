# app/services/selector.py

from __future__ import annotations
from datetime import datetime, date
from typing import List, Tuple, Optional
from sqlalchemy import select, func, exists, and_
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo
from app.db.models import Subscription, Tip, Topic, Delivery

# ==============================
# Tip Selection Service
# ==============================
# This module contains the selection logic for choosing which tips
# each user receives daily. It ensures fair rotation, avoids duplicates,
# and supports fallback logic when all tips have been delivered.

# ------------------------------
# Daily rotation utility
# ------------------------------


def _daily_index(seed_date: date, user_id: int, topic_id: int, modulo: int) -> int:
    """
    Deterministic index generator based on date, user_id, and topic_id.
    Used for consistent daily rotation (same tip per day for same user/topic).
    """
    seed = int(seed_date.strftime("%Y%m%d")) ^ (
        user_id * 2654435761
    ) ^ (topic_id * 11400714819323198485 % (1 << 31))
    return abs(seed) % max(1, modulo)


# ------------------------------
# Basic selection helpers
# ------------------------------
def get_user_subscribed_topics(db: Session, user_id: int) -> List[Topic]:
    """
    Return all active topics that the user is subscribed to.
    Both the subscription and the topic must be active.
    """
    q = (
        select(Topic)
        .join(Subscription, Subscription.topic_id == Topic.id)
        .where(
            Subscription.user_id == user_id,
            Subscription.is_active == True,  # noqa: E712
            Topic.is_active == True,
        )
        .order_by(Topic.name.asc())
    )
    return list(db.scalars(q))


def _tips_not_delivered_query(user_id: int, topic_id: int):
    """
    Base subquery: all tips in the topic that have NEVER been delivered to the user.
    (Respects the unique constraint tip_id + user_id in the Delivery table.)
    """
    delivered_exists = (
        select(Delivery.id)
        .where(and_(Delivery.tip_id == Tip.id, Delivery.user_id == user_id))
        .limit(1)
    )
    return select(Tip).where(Tip.topic_id == topic_id, ~exists(delivered_exists))


def _pick_many_from_query(db: Session, base_q, limit: int, strategy: str) -> List[Tip]:
    """
    Pick multiple tips from a query, ordered by the given strategy:
    - 'random': random order
    - 'latest': most recently created (default)
    """
    if strategy == "random":
        q = base_q.order_by(func.random()).limit(limit)
    else:
        q = base_q.order_by(Tip.created_at.desc(), Tip.id.desc()).limit(limit)
    return list(db.scalars(q))


# ------------------------------
# Core selection API
# ------------------------------
def pick_tip_for_topic(
    db: Session,
    user_id: int,
    topic_id: int,
    strategy: str = "latest",
    tz_name: str = "Europe/Madrid",
) -> Optional[Tip]:
    """
    Pick a single NON-delivered tip for a topic and user.
    If no undelivered tips remain, fallback to deterministic rotation
    based on date and user/topic combination.
    This function does NOT write deliveries (read-only selection).
    """
    # 1) Try to pick a non-delivered tip first
    base_q = _tips_not_delivered_query(user_id, topic_id)
    tip = db.scalars(
        base_q.order_by(func.random()).limit(1)
        if strategy == "random"
        else base_q.order_by(Tip.created_at.desc(), Tip.id.desc()).limit(1)
    ).first()
    if tip:
        return tip

    # 2) Fallback: deterministic rotation over all tips for this topic
    tz = ZoneInfo(tz_name)
    today_local = datetime.now(tz).date()
    all_q = select(Tip).where(Tip.topic_id == topic_id).order_by(
        Tip.created_at.asc(), Tip.id.asc()
    )
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
    topics_override: Optional[List[Topic]] = None,
) -> List[Tuple[Topic, List[Tip]]]:
    """
    Return a bundle of (topic, [tips]) for each subscribed topic.
    Prioritizes non-delivered tips, then falls back to daily rotation.
    Does NOT create deliveries (read-only).
    """
    topics = topics_override if topics_override is not None else get_user_subscribed_topics(
        db, user_id
    )
    bundle: List[Tuple[Topic, List[Tip]]] = []

    for topic in topics:
        picks: List[Tip] = []

        # Try to get undelivered tips first
        base_q = _tips_not_delivered_query(user_id, topic.id)
        remaining = _pick_many_from_query(db, base_q, per_topic, strategy)
        picks.extend(remaining)

        # If not enough undelivered tips, apply deterministic rotation fallback
        if len(picks) < per_topic:
            tz = ZoneInfo(tz_name)
            today_local = datetime.now(tz).date()
            all_q = select(Tip).where(Tip.topic_id == topic.id).order_by(
                Tip.created_at.asc(), Tip.id.asc()
            )
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

        # Add the topic and its selected tips to the final bundle
        if picks:
            bundle.append((topic, picks))

    return bundle


def count_remaining_by_topic(db: Session, user_id: int) -> List[Tuple[Topic, int]]:
    """
    For each subscribed topic, return how many non-delivered tips remain.
    """
    topics = get_user_subscribed_topics(db, user_id)
    out: List[Tuple[Topic, int]] = []

    for topic in topics:
        base_q = _tips_not_delivered_query(user_id, topic.id)
        remaining = db.execute(select(func.count()).select_from(
            base_q.subquery())).scalar() or 0
        out.append((topic, int(remaining)))

    return out


# ------------------------------
# Compatibility wrapper (legacy API)
# ------------------------------
def get_today_tips_for_user(
    db: Session,
    user_id: int,
    tz_name: str = "Europe/Madrid",
    per_topic: int = 1,
) -> Tuple[date, List[Tip]]:
    """
    Maintains the original function signature for backward compatibility.
    Prioritizes non-delivered tips and applies deterministic fallback rotation.
    Returns a tuple: (today_date, [tips]).
    """
    tz = ZoneInfo(tz_name)
    today_local = datetime.now(tz).date()

    # Get a daily bundle of tips per topic
    bundle = pick_daily_bundle(
        db=db,
        user_id=user_id,
        per_topic=per_topic,
        strategy="latest",
        tz_name=tz_name,
    )

    # Flatten the bundle into a single list of tips
    flat_tips: List[Tip] = []
    for _, picks in bundle:
        flat_tips.extend(picks)

    return today_local, flat_tips
