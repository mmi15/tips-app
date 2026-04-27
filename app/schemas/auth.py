from pydantic import BaseModel, EmailStr, ConfigDict

# ==============================
# Authentication Schemas
# ==============================
# These models define the data structures used for
# login, registration, token responses, and user info.
# They are used by FastAPI for automatic validation.

# ------------------------------
# JWT Token response schema
# ------------------------------


class Token(BaseModel):
    # The actual access token (usually a JWT)
    access_token: str
    # Type of token (default: "bearer")
    token_type: str = "bearer"


# ------------------------------
# Login request schema
# ------------------------------
class LoginInput(BaseModel):
    # User's email (must be a valid email format)
    email: EmailStr
    # User's password in plain text (validated internally)
    password: str


# ------------------------------
# Registration request schema
# ------------------------------
class RegisterInput(BaseModel):
    # Email for new account
    email: EmailStr
    # Password for new account
    password: str


# ------------------------------
# User profile schema (for /me endpoints)
# ------------------------------
class MeRead(BaseModel):
    # Unique user ID from the database
    id: int
    # User's email
    email: EmailStr

    # Allow Pydantic to build the model directly
    # from ORM objects (e.g., SQLAlchemy instances)
    model_config = ConfigDict(from_attributes=True)
