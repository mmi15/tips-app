from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import User
from app.api.deps import require_admin
from app.schemas.tip import TipList, TipRead
from app.services.tips import list_tips, get_tip


# Create an APIRouter instance for admin-related endpoints
# All routes defined here will have the prefix "/admin"
router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/users/{user_id}/promote", status_code=204)
def promote_user(
    user_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin)
):
    """
    Promote a regular user to admin.

    - Only accessible to existing admins (require_admin dependency).
    - Looks up the user by ID.
    - If the user doesn't exist, raises 404.
    - If the user is already admin, raises 400.
    - Otherwise, sets user.is_admin = True and commits the change.
    """
    user = db.execute(select(User).where(
        User.id == user_id)).scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is already admin")

    user.is_admin = True
    db.add(user)
    db.commit()
    return


@router.post("/users/{user_id}/demote", status_code=status.HTTP_204_NO_CONTENT)
def demote_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(require_admin),
):
    """
    Demote an admin back to a regular user.

    - Only accessible to admins (require_admin dependency).
    - Looks up the user by ID.
    - If the user doesn't exist, raises 404.
    - Prevents an admin from demoting themselves (400).
    - If the user is not currently admin, raises 400.
    - Otherwise, sets user.is_admin = False and commits the change.
    """
    user = db.execute(select(User).where(
        User.id == user_id)).scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.id == current_admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="You cannot demote yourself")

    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is not an admin")

    user.is_admin = False
    db.add(user)
    db.commit()
    return


@router.get("/tips", response_model=TipList)
def list_tips_for_admin(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    topic_id: int | None = Query(None),
    status_filter: str | None = Query(
        None, pattern="^(draft|published|hidden)$", alias="status"),
    q: str | None = Query(None, description="Search in title/body"),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    items, total = list_tips(
        db, page=page, size=size, topic_id=topic_id, status=status_filter, q=q
    )
    return TipList(total=total, page=page, size=size, items=items)


@router.patch("/tips/{tip_id}/status", response_model=TipRead)
def update_tip_status(
    tip_id: int,
    status_value: str = Query(..., pattern="^(draft|published|hidden)$", alias="status"),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    tip = get_tip(db, tip_id)
    if not tip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tip not found")
    tip.status = status_value
    db.add(tip)
    db.commit()
    db.refresh(tip)
    return tip
