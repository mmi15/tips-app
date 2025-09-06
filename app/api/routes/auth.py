from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.db.session import get_db
from app.db import models
from app.core.security import hash_password, verify_password, create_access_token
from app.schemas.auth import Token, LoginInput, RegisterInput, MeRead
from app.api.deps import get_current_active_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=MeRead, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterInput, db: Session = Depends(get_db)):
    user = models.User(email=payload.email,
                       hashed_password=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, detail="User with this email already exists.")
    db.refresh(user)
    return user

# Option A: JSON body login (recommended for API clients)


@router.post("/login", response_model=Token)
def login_json(payload: LoginInput, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=400, detail="Incorrect email or password.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive.")
    token = create_access_token(subject=user.id)
    return {"access_token": token, "token_type": "bearer"}

# Option B: OAuth2PasswordRequestForm (for Swagger's built-in flow)


@router.post("/login-form", response_model=Token, include_in_schema=False)
def login_form(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # form.username carries the email
    user = db.query(models.User).filter(
        models.User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=400, detail="Incorrect email or password.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User is inactive.")
    token = create_access_token(subject=user.id)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=MeRead)
def read_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user
