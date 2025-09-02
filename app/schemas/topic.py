from pydantic import BaseModel, ConfigDict
from typing import Optional


class TopicCreate(BaseModel):
    name: str
    slug: str


class TopicUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None


class TopicRead(BaseModel):
    id: int
    name: str
    slug: str

    # Pydantic v2: enable reading from SQLAlchemy objects
    model_config = ConfigDict(from_attributes=True)
