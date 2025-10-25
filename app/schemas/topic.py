# app/schemas/topic.py

from pydantic import BaseModel, ConfigDict
from typing import Optional

# ==============================
# Topic Schemas
# ==============================
# These models define the data structures used for
# creating, updating, and reading topic information.
# Topics represent the content categories users can subscribe to.

# ------------------------------
# Schema for creating a new topic
# ------------------------------


class TopicCreate(BaseModel):
    # Topic name (e.g., "Nutrition", "History")
    name: str
    # URL-friendly version of the topic name
    slug: str
    # Whether the topic is active (default: True)
    is_active: bool = True


# ------------------------------
# Schema for updating an existing topic
# ------------------------------
class TopicUpdate(BaseModel):
    # Optional new name for the topic
    name: Optional[str] = None
    # Optional new slug for the topic
    slug: Optional[str] = None
    # Optional status change (activate/deactivate)
    is_active: Optional[bool] = None


# ------------------------------
# Schema for reading topic data
# ------------------------------
class TopicRead(BaseModel):
    # Unique topic ID
    id: int
    # Topic name
    name: str
    # URL slug
    slug: str
    # Indicates whether the topic is active
    is_active: bool

    # Allow building this model directly from ORM (SQLAlchemy) objects
    model_config = ConfigDict(from_attributes=True)
