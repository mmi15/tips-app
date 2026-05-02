"""Límites free/premium para selección de tips (sin tocar la BD)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.selector import get_user_subscribed_topics


def apply_plan_policy(
    db: Session,
    user,
    requested_per_topic: int,
) -> tuple[list, int]:
    """
    Free (default): máx. 3 temas y 1 tip por tema.
    Premium provisional: user.is_admin == True.
    Devuelve (topics_permitidos, per_topic_efectivo).
    """
    is_premium = bool(getattr(user, "is_admin", False))
    all_topics = get_user_subscribed_topics(db, user.id)

    if is_premium:
        per_topic_effective = requested_per_topic
        topics_allowed = all_topics
    else:
        per_topic_effective = 1
        topics_sorted = sorted(
            all_topics, key=lambda t: (t.name or "", t.slug or ""))
        topics_allowed = topics_sorted[:3]

    return topics_allowed, per_topic_effective
