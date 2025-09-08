# app/schemas/tip.py
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl


class TipBase(BaseModel):
    topic_id: int
    title: str = Field(..., max_length=255)
    body: str = Field(..., max_length=5000)
    source_url: Optional[HttpUrl] = None


class TipCreate(TipBase):
    fingerprint: Optional[str] = None


class TipUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    body: Optional[str] = Field(None, max_length=5000)
    source_url: Optional[HttpUrl] = None


class TipRead(BaseModel):
    id: int
    topic_id: int
    title: str
    body: str
    source_url: Optional[str]
    fingerprint: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TipList(BaseModel):
    total: int
    page: int
    size: int
    items: List[TipRead]
