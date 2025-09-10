# app/api/routes/me.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.api.deps import get_current_active_user
from app.schemas.tip import TodayTips, TipRead
from app.services.selector import get_today_tips_for_user

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
    today_date, tips = get_today_tips_for_user(
        db, user_id=current_user.id, tz_name=tz, per_topic=per_topic)
    items = [TipRead.model_validate(t) for t in tips]
    return TodayTips(date=today_date, count=len(items), items=items)
