from pydantic import BaseModel, ConfigDict


class SubscriptionCreate(BaseModel):
    user_id: int
    topic_id: int


class SubscriptionRead(BaseModel):
    id: int
    user_id: int
    topic_id: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)
