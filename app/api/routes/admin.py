from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import User
from app.api.deps import require_admin


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
