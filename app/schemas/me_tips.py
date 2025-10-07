# app/schemas/me_tips.py
from __future__ import annotations
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# Bloque Tip básico (reutilizable)


class TipLite(BaseModel):
    id: int
    title: str
    body: str
    source_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TopicLite(BaseModel):
    id: int
    name: str
    slug: str

    class Config:
        from_attributes = True


# /me/tips/today
class TodayTopicTips(BaseModel):
    topic: TopicLite
    tips: List[TipLite]


class TodayResponse(BaseModel):
    user_id: int
    count: int = Field(ge=0)
    deliveries_created: int = Field(ge=0)
    data: List[TodayTopicTips]


# /me/tips/history
class HistoryItem(BaseModel):
    delivery_id: int
    delivered_at: datetime
    channel: str
    status: str
    tip: TipLite
    topic: TopicLite


class HistoryList(BaseModel):
    user_id: int
    page: int
    size: int
    total: int
    items: List[HistoryItem]


class DeliveryStatusResponse(BaseModel):
    delivery_id: int
    delivered_at: datetime
    channel: str
    status: str
    tip: TipLite
    topic: TopicLite
