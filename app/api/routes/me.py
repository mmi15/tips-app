# app/api/routes/me.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo

from app.db.session import get_db
from app.api.deps import get_current_active_user
from app.schemas.tip import TodayTips, TipRead
from app.schemas.me_tips import HistoryList, DeliveryStatusResponse

from app.services.tips import (
    register_deliveries_if_missing,
    get_delivery_history,
    mark_delivery_read,
)
from app.services.selector import (
    pick_daily_bundle,
    get_user_subscribed_topics,
)


# Router for "me" (current authenticated user) endpoints.
router = APIRouter(prefix="/me", tags=["me"])


@router.get("/tips/today", response_model=TodayTips)
def get_my_today_tips(
    # Optional IANA timezone. Used to compute "today" for the user.
    tz: Optional[str] = Query(
        "Europe/Madrid", description="Zona horaria IANA, ej. Europe/Madrid"),
    # Desired number of tips per topic (clamped by plan policy later).
    per_topic: int = Query(
        1, ge=1, le=5, description="Número de tips por topic (rotados)"),
    # DB session injected per-request.
    db: Session = Depends(get_db),
    # Current authenticated and active user (JWT-based).
    current_user=Depends(get_current_active_user),
):
    # 1) Apply plan limits (free vs premium), without mutating DB.
    topics_allowed, per_topic_effective = apply_plan_policy(
        db, current_user, per_topic)

    # 2) Select the daily bundle (read-only selection logic).
    #    Strategy "latest" prioritizes non-delivered tips and falls back deterministically.
    bundle = pick_daily_bundle(
        db=db,
        user_id=current_user.id,
        per_topic=per_topic_effective,
        strategy="latest",
        tz_name=tz,
        topics_override=topics_allowed,
    )

    # 3) Register deliveries idempotently (UNIQUE on (tip_id, user_id) enforced in DB).
    tips_flat = [tip for _, tips_list in bundle for tip in tips_list]
    _created = register_deliveries_if_missing(
        db, user_id=current_user.id, tips=tips_flat, channel="app", status="sent"
    )

    # Build response items as Pydantic models.
    items = [TipRead.model_validate(t) for t in tips_flat]
    # TodayTips intentionally omits plan metadata to keep the response stable.
    return TodayTips(date=datetime.now(ZoneInfo(tz)).date(), count=len(items), items=items)


@router.get("/tips/history", response_model=HistoryList)
def get_my_tips_history(
    # Pagination params (1-based page index).
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    # Optional topic filter.
    topic_id: Optional[int] = Query(
        None, description="Filtrar por topic_id"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    # Fetch paginated delivery history for the current user (optionally filtered by topic).
    items, total = get_delivery_history(
        db,
        user_id=current_user.id,
        page=page,
        size=size,
        topic_id=topic_id,
    )
    # Return a typed, paginated response.
    return HistoryList(user_id=current_user.id, page=page, size=size, total=total, items=items)


@router.patch("/tips/{delivery_id}/read", response_model=DeliveryStatusResponse)
def mark_tip_as_read(
    # Delivery (sent tip) identifier to mark as read.
    delivery_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    # Delegate to service layer to validate ownership and update read status.
    return mark_delivery_read(db, user_id=current_user.id, delivery_id=delivery_id)


def apply_plan_policy(
    db: Session,
    user,
    requested_per_topic: int,
) -> tuple[list, int]:
    """
    Apply plan limits without touching the DB:
    - Free (default): max 3 topics and 1 tip per topic.
    - Temporary Premium: user.is_admin == True (until we have a proper plan field).
    Returns (allowed_topics, effective_per_topic).
    """
    # Temporary premium flag: treat admins as premium until a real plan model exists.
    is_premium = bool(getattr(user, "is_admin", False))

    # Fetch all topics the user is currently subscribed to.
    all_topics = get_user_subscribed_topics(db, user.id)

    if is_premium:
        # Premium: no limits; honor the requested per-topic count.
        per_topic_effective = requested_per_topic
        topics_allowed = all_topics
    else:
        # Free: enforce strict limits.
        per_topic_effective = 1
        # Deterministically pick up to 3 topics (sorted by name/slug for stable selection).
        topics_sorted = sorted(
            all_topics, key=lambda t: (t.name or "", t.slug or ""))
        topics_allowed = topics_sorted[:3]

    return topics_allowed, per_topic_effective
