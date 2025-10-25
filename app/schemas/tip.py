# app/schemas/tip.py

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl

# ==============================
# Tip Schemas
# ==============================
# These models define the data structures used for
# creating, updating, listing, and reading tips.
# They are used by FastAPI for both input validation
# and response serialization.

# ------------------------------
# Base schema (shared attributes)
# ------------------------------


class TipBase(BaseModel):
    # Topic ID the tip belongs to
    topic_id: int
    # Tip title (max 255 characters)
    title: str = Field(..., max_length=255)
    # Tip content/body (max 5000 characters)
    body: str = Field(..., max_length=5000)
    # Optional source link for the tip
    source_url: Optional[HttpUrl] = None


# ------------------------------
# Schema for creating a new tip
# ------------------------------
class TipCreate(TipBase):
    # Optional unique fingerprint used for deduplication
    fingerprint: Optional[str] = None


# ------------------------------
# Schema for updating an existing tip
# ------------------------------
class TipUpdate(BaseModel):
    # Optional new title (if provided)
    title: Optional[str] = Field(None, max_length=255)
    # Optional new body text (if provided)
    body: Optional[str] = Field(None, max_length=5000)
    # Optional new source URL
    source_url: Optional[HttpUrl] = None


# ------------------------------
# Schema for reading a tip from the database
# ------------------------------
class TipRead(BaseModel):
    # Unique tip ID
    id: int
    # Related topic ID
    topic_id: int
    # Tip title
    title: str
    # Tip content
    body: str
    # Optional source link
    source_url: Optional[str]
    # Optional fingerprint (for deduplication)
    fingerprint: Optional[str]
    # Timestamp when the tip was created
    created_at: datetime

    class Config:
        # Allow Pydantic to build this model directly from ORM objects
        from_attributes = True


# ------------------------------
# Schema for paginated tip lists
# ------------------------------
class TipList(BaseModel):
    # Total number of tips in the dataset
    total: int
    # Current page number
    page: int
    # Number of items per page
    size: int
    # List of tips (as TipRead models)
    items: List[TipRead]


# ------------------------------
# Schema for today's tips
# ------------------------------
class TodayTips(BaseModel):
    # Date the tips were generated or delivered
    date: datetime
    # Total number of tips returned
    count: int
    # List of today's tips
    items: List[TipRead]
