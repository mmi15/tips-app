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


router = APIRouter(prefix="/me", tags=["me"])


@router.get("/tips/today", response_model=TodayTips)
def get_my_today_tips(
    tz: Optional[str] = Query(
        "Europe/Madrid", description="Zona horaria IANA, ej. Europe/Madrid"),
    per_topic: int = Query(
        1, ge=1, le=5, description="Número de tips por topic (rotados)"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    # 1) Aplica política de plan
    topics_allowed, per_topic_effective = apply_plan_policy(
        db, current_user, per_topic)

    # 2) Selección (solo lectura; prioriza no entregados y hace fallback determinista)
    bundle = pick_daily_bundle(
        db=db,
        user_id=current_user.id,
        per_topic=per_topic_effective,
        strategy="latest",
        tz_name=tz,
        topics_override=topics_allowed,
    )

    # 3) Registrar entregas respetando UNIQUE (tip_id, user_id)
    tips_flat = [tip for _, tips_list in bundle for tip in tips_list]
    _created = register_deliveries_if_missing(
        db, user_id=current_user.id, tips=tips_flat, channel="app", status="sent"
    )

    items = [TipRead.model_validate(t) for t in tips_flat]
    # TodayTips no incluye metadatos de plan; mantenemos respuesta estable
    return TodayTips(date=datetime.now(ZoneInfo(tz)).date(), count=len(items), items=items)


@router.get("/tips/history", response_model=HistoryList)
def get_my_tips_history(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    topic_id: Optional[int] = Query(
        None, description="Filtrar por topic_id"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    items, total = get_delivery_history(
        db,
        user_id=current_user.id,
        page=page,
        size=size,
        topic_id=topic_id,
    )
    return HistoryList(user_id=current_user.id, page=page, size=size, total=total, items=items)


@router.patch("/tips/{delivery_id}/read", response_model=DeliveryStatusResponse)
def mark_tip_as_read(
    delivery_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    return mark_delivery_read(db, user_id=current_user.id, delivery_id=delivery_id)


def apply_plan_policy(
    db: Session,
    user,
    requested_per_topic: int,
) -> tuple[list, int]:
    """
    Aplica límites por plan sin tocar BD:
    - Free (por defecto): máx 3 topics y 1 tip por topic.
    - Premium provisional: user.is_admin == True.
    Devuelve (topics_permitidos, per_topic_efectivo).
    """
    # Plan: premium si admin (temporal hasta tener campo plan en BD)
    is_premium = bool(getattr(user, "is_admin", False))

    # Recoge todos los topics a los que el usuario está suscrito
    all_topics = get_user_subscribed_topics(db, user.id)

    if is_premium:
        # Premium: sin límites / respeta lo pedido
        per_topic_effective = requested_per_topic
        topics_allowed = all_topics
    else:
        # Free: clamp
        per_topic_effective = 1
        # Tomamos máx 3 topics de forma determinista (por nombre/slug)
        topics_sorted = sorted(
            all_topics, key=lambda t: (t.name or "", t.slug or ""))
        topics_allowed = topics_sorted[:3]

    return topics_allowed, per_topic_effective
