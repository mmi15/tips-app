from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db import models
from app.core.security import get_subject_from_token


# OAuth2 scheme used for authentication.
# It expects a Bearer token in the "Authorization" header.
# Example: Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    """
    Dependency that extracts the current user from the provided JWT token.

    1. Retrieves the token from the request header.
    2. Decodes it using get_subject_from_token() to extract the subject (user ID).
    3. Queries the database to get the corresponding User.
    4. Raises an HTTP 401 if the token is invalid or user not found.
    """
    sub = get_subject_from_token(token)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
    user = db.query(models.User).get(int(sub))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
    return user


def get_current_active_user(user: models.User = Depends(get_current_user)) -> models.User:
    """
    Dependency that ensures the current user is active.

    - It depends on get_current_user.
    - If the user is inactive (is_active == False), it raises HTTP 403.
    - Returns the active user otherwise.
    """
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user.")
    return user


def require_admin(current_user=Depends(get_current_active_user)):
    """
    Dependency that ensures the current user has admin privileges.

    - It depends on get_current_active_user.
    - Checks the 'is_admin' attribute of the user.
    - If not admin, raises HTTP 403 Forbidden.
    - Returns the current user if admin.
    """
    if not getattr(current_user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return current_user
