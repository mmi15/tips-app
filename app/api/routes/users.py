from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.hash import bcrypt

from app.db.session import get_db
from app.db import models
from app.schemas.user import UserCreate, UserUpdate, UserRead

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    hashed = bcrypt.hash(payload.password)
    user = models.User(email=payload.email,
                       hashed_password=hashed, is_active=payload.is_active)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="User with this email already exists.")
    db.refresh(user)
    return user


@router.get("", response_model=list[UserRead])
def list_users(skip: int = 0, limit: int = 50, only_active: bool = False, db: Session = Depends(get_db)):
    q = db.query(models.User)
    if only_active:
        q = q.filter(models.User.is_active.is_(True))
    return q.offset(skip).limit(limit).all()


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@router.patch("/{user_id}", response_model=UserRead)
def patch_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if payload.email is not None:
        user.email = payload.email
    if payload.password is not None:
        user.hashed_password = bcrypt.hash(payload.password)
    if payload.is_active is not None:
        user.is_active = payload.is_active
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="User with this email already exists.")
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    db.delete(user)
    db.commit()
    return None
