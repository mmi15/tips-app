# app/api/routes/tips.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.schemas.tip import TipCreate, TipRead, TipUpdate, TipList
from app.services.tips import (
    create_tip, get_tip, list_tips, update_tip, hard_delete_tip
)
from app.api.deps import get_current_active_user, require_admin

router = APIRouter(prefix="/tips", tags=["tips"])


@router.get("", response_model=TipList)
def list_tips_endpoint(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    topic_id: Optional[int] = Query(None),
    q: Optional[str] = Query(None, description="Buscar en título/cuerpo"),
    db: Session = Depends(get_db),
):
    items, total = list_tips(db, page=page, size=size, topic_id=topic_id, q=q)
    return TipList(total=total, page=page, size=size, items=items)


@router.get("/{tip_id}", response_model=TipRead)
def get_tip_endpoint(tip_id: int, db: Session = Depends(get_db)):
    tip = get_tip(db, tip_id)
    if not tip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tip not found")
    return tip


@router.post("", response_model=TipRead, status_code=status.HTTP_201_CREATED)
def create_tip_endpoint(
    payload: TipCreate,
    db: Session = Depends(get_db),
    _user=Depends(get_current_active_user),
    _admin=Depends(require_admin),
):
    try:
        return create_tip(db, payload)
    except ValueError as e:

        msg = str(e)
        code = status.HTTP_400_BAD_REQUEST if "Topic" in msg else status.HTTP_409_CONFLICT
        raise HTTPException(status_code=code, detail=msg)


@router.patch("/{tip_id}", response_model=TipRead)
def update_tip_endpoint(
    tip_id: int,
    payload: TipUpdate,
    db: Session = Depends(get_db),
    _user=Depends(get_current_active_user),
    _admin=Depends(require_admin)
):
    tip = get_tip(db, tip_id)
    if not tip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tip not found")
    return update_tip(db, tip, payload)


@router.delete("/{tip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tip_endpoint(
    tip_id: int,
    db: Session = Depends(get_db),
    _user=Depends(get_current_active_user),
    _admin=Depends(require_admin),
):
    tip = get_tip(db, tip_id)
    if not tip:
        return
    hard_delete_tip(db, tip_id)
