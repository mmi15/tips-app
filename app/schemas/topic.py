from pydantic import BaseModel, ConfigDict
from typing import Optional


class TopicCreate(BaseModel):
    name: str
    slug: str
    is_active: bool = True


class TopicUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    is_active: Optional[bool] = None


class TopicRead(BaseModel):
    id: int
    name: str
    slug: str
    is_active: bool
    # Pydantic v2: enable reading from SQLAlchemy objects
    model_config = ConfigDict(from_attributes=True)
