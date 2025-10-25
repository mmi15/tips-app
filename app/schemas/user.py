# app/schemas/user.py

from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict

# ==============================
# User Schemas
# ==============================
# These models define the data structures used for
# creating, updating, and reading user information.
# They are used by FastAPI for input validation and response serialization.

# ------------------------------
# Schema for creating a new user
# ------------------------------


class UserCreate(BaseModel):
    # User's email address (validated format)
    email: EmailStr
    # Plain-text password (will be hashed before saving)
    password: str
    # Whether the account is active (default: True)
    is_active: bool = True


# ------------------------------
# Schema for updating an existing user
# ------------------------------
class UserUpdate(BaseModel):
    # Optional new email address
    email: Optional[EmailStr] = None
    # Optional new password
    password: Optional[str] = None
    # Optional change to account status (active/inactive)
    is_active: Optional[bool] = None


# ------------------------------
# Schema for reading user data
# ------------------------------
class UserRead(BaseModel):
    # Unique user ID
    id: int
    # User's email address
    email: EmailStr
    # Indicates whether the user is active
    is_active: bool
    # Indicates whether the user has admin privileges
    is_admin: bool

    # Allow Pydantic to build this model directly from ORM (SQLAlchemy) objects
    model_config = ConfigDict(from_attributes=True)
