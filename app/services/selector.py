# app/services/selector.py
from __future__ import annotations
from datetime import datetime, date
from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select
from zoneinfo import ZoneInfo  # pip install tzdata en Windows

from app.db.models import Subscription, Tip


def _daily_index(seed_date: date, user_id: int, topic_id: int, modulo: int) -> int:

    seed = int(seed_date.strftime("%Y%m%d")) ^ (
        user_id * 2654435761) ^ (topic_id * 11400714819323198485 % (1 << 31))
    return abs(seed) % max(1, modulo)


def get_today_tips_for_user(
    db: Session,
    user_id: int,
    tz_name: str = "Europe/Madrid",
    per_topic: int = 1,
) -> Tuple[date, List[Tip]]:
    """
    Selecciona hasta `per_topic` tips por cada topic suscrito, rotando diariamente de forma determinística.
    No requiere campos extra en BD. Si un topic no tiene tips, se omite.
    """

    tz = ZoneInfo(tz_name)
    today_local = datetime.now(tz).date()

    subq = select(Subscription.topic_id).where(
        Subscription.user_id == user_id).subquery()

    tips = db.execute(
        select(Tip).where(Tip.topic_id.in_(select(subq.c.topic_id))
                          ).order_by(Tip.topic_id, Tip.created_at.asc())
    ).scalars().all()

    by_topic = {}
    for t in tips:
        by_topic.setdefault(t.topic_id, []).append(t)

    selected: List[Tip] = []
    for topic_id, lst in by_topic.items():
        if not lst:
            continue
        idx = _daily_index(today_local, user_id, topic_id, len(lst))
        selected.append(lst[idx])

    return today_local, selected
