from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from passlib.hash import bcrypt

from app.db.session import get_db
from app.db import models
from app.schemas.user import UserCreate, UserUpdate, UserRead

# Create router for user-related endpoints
router = APIRouter(prefix="/users", tags=["users"])


# Create a new user
@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    # Hash the user's password before storing
    hashed = bcrypt.hash(payload.password)
    user = models.User(email=payload.email,
                       hashed_password=hashed, is_active=payload.is_active)
    db.add(user)
    try:
        db.commit()  # Save new user to database
    except IntegrityError:
        db.rollback()  # Undo transaction if duplicate email
        raise HTTPException(
            status_code=400, detail="User with this email already exists.")
    db.refresh(user)  # Reload user with DB-generated ID
    return user


# List all users (with optional pagination and active filter)
@router.get("", response_model=list[UserRead])
def list_users(skip: int = 0, limit: int = 50, only_active: bool = False, db: Session = Depends(get_db)):
    q = db.query(models.User)
    # Optionally return only active users
    if only_active:
        q = q.filter(models.User.is_active.is_(True))
    # Apply pagination
    return q.offset(skip).limit(limit).all()


# Get a single user by ID
@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).get(user_id)
    if not user:
        # Return 404 if user not found
        raise HTTPException(status_code=404, detail="User not found.")
    return user


# Partially update user fields (email, password, or is_active)
@router.patch("/{user_id}", response_model=UserRead)
def patch_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    # Update fields only if provided
    if payload.email is not None:
        user.email = payload.email
    if payload.password is not None:
        user.hashed_password = bcrypt.hash(payload.password)
    if payload.is_active is not None:
        user.is_active = payload.is_active
    try:
        db.commit()  # Save changes
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="User with this email already exists.")
    db.refresh(user)  # Refresh to get latest DB state
    return user


# Delete a user by ID
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    db.delete(user)
    db.commit()  # Permanently remove user
    return None
