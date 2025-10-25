# app/schemas/subscription.py

from pydantic import BaseModel, ConfigDict

# ==============================
# Subscription Schemas
# ==============================
# These models define the data structures used for
# creating and reading user subscriptions to topics.

# ------------------------------
# Schema for creating a subscription
# ------------------------------


class SubscriptionCreate(BaseModel):
    # ID of the user who subscribes
    user_id: int
    # ID of the topic being subscribed to
    topic_id: int


# ------------------------------
# Schema for reading an existing subscription
# ------------------------------
class SubscriptionRead(BaseModel):
    # Unique subscription ID
    id: int
    # ID of the subscribed user
    user_id: int
    # ID of the topic subscribed to
    topic_id: int
    # Indicates whether the subscription is active
    is_active: bool

    # Allow Pydantic to build this model directly
    # from ORM (SQLAlchemy) objects
    model_config = ConfigDict(from_attributes=True)
