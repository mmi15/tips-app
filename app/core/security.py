from datetime import datetime, timedelta, timezone
from typing import Optional, Any, Dict

from jose import jwt, JWTError
from passlib.hash import bcrypt

from app.core.config import settings


# -------------------------------
# PASSWORD HASHING
# -------------------------------

# Hash a plain-text password using bcrypt
def hash_password(password: str) -> str:
    return bcrypt.hash(password)


# Verify a plain-text password against its hashed version
def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.verify(password, hashed)


# -------------------------------
# JWT (JSON Web Tokens)
# -------------------------------

# Create a signed access token with expiration and optional custom claims
def create_access_token(
    subject: str | int,
    expires_minutes: int | None = None,
    extra_claims: Dict[str, Any] | None = None,
) -> str:
    # Use default expiration time if none provided
    if expires_minutes is None:
        expires_minutes = settings.access_token_expire_minutes

    # Current UTC time
    now = datetime.now(tz=timezone.utc)

    # Token expiration time
    expire = now + timedelta(minutes=expires_minutes)

    # Base payload: subject, issued-at, expiration
    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    # Include any extra claims if provided
    if extra_claims:
        to_encode.update(extra_claims)

    # Encode and sign the JWT using app settings
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


# Decode and validate a JWT token
def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


# Extract the "subject" (user ID or email) from a valid token
def get_subject_from_token(token: str) -> Optional[str]:
    try:
        payload = decode_token(token)
        return payload.get("sub")
    except JWTError:
        # Return None if the token is invalid or expired
        return None
