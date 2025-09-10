from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import User
from app.api.deps import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/users/{user_id}/promote", status_code=204)
def promote_user(
    user_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin)
):
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
