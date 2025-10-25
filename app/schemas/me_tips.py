# app/schemas/me_tips.py

from __future__ import annotations
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# ==============================
# Schemas for user tips (/me/tips)
# ==============================
# These models define the data structures used for
# daily tips, delivery history, and status updates.
# All models are designed for Pydantic + FastAPI serialization.

# ------------------------------
# Reusable basic tip schema
# ------------------------------


class TipLite(BaseModel):
    # Unique tip ID
    id: int
    # Tip title
    title: str
    # Tip content/body
    body: str
    # Optional source link (if available)
    source_url: Optional[str] = None
    # When the tip was created or generated
    created_at: datetime

    class Config:
        # Allow building model directly from ORM objects
        from_attributes = True


# ------------------------------
# Reusable basic topic schema
# ------------------------------
class TopicLite(BaseModel):
    # Unique topic ID
    id: int
    # Topic name (human-readable)
    name: str
    # Slug version (URL-friendly)
    slug: str

    class Config:
        # Allow building model directly from ORM objects
        from_attributes = True


# ------------------------------
# /me/tips/today response schemas
# ------------------------------
class TodayTopicTips(BaseModel):
    # The topic information
    topic: TopicLite
    # List of tips for this topic (usually 1 per day)
    tips: List[TipLite]


class TodayResponse(BaseModel):
    # The user's ID
    user_id: int
    # Total number of tips returned
    count: int = Field(ge=0)
    # Number of new deliveries created for today
    deliveries_created: int = Field(ge=0)
    # List of topics and their respective tips
    data: List[TodayTopicTips]


# ------------------------------
# /me/tips/history response schemas
# ------------------------------
class HistoryItem(BaseModel):
    # Delivery record ID
    delivery_id: int
    # Date and time the tip was delivered
    delivered_at: datetime
    # Channel used (e.g., "app", "email")
    channel: str
    # Status of the delivery ("read", "unread", etc.)
    status: str
    # The delivered tip
    tip: TipLite
    # The related topic
    topic: TopicLite


class HistoryList(BaseModel):
    # The user's ID
    user_id: int
    # Current page number
    page: int
    # Number of items per page
    size: int
    # Total number of items in the history
    total: int
    # Paginated list of history entries
    items: List[HistoryItem]


# ------------------------------
# Response for delivery status updates
# ------------------------------
class DeliveryStatusResponse(BaseModel):
    # Delivery record ID
    delivery_id: int
    # Date and time the delivery occurred
    delivered_at: datetime
    # Delivery channel
    channel: str
    # Current delivery status
    status: str
    # The tip data
    tip: TipLite
    # The associated topic
    topic: TopicLite
