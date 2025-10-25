from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    String, Integer, Boolean, DateTime, ForeignKey, Text,
    UniqueConstraint, Index
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# Base class for all SQLAlchemy models
class Base(DeclarativeBase):
    """Declarative base class."""
    pass


# -------------------------------
# USER MODEL
# -------------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False)
    is_admin: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0")

    # Relationships
    subscriptions: Mapped[List["Subscription"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    deliveries: Mapped[List["Delivery"]] = relationship(back_populates="user")


# -------------------------------
# TOPIC MODEL
# -------------------------------
class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    tips: Mapped[List["Tip"]] = relationship(
        back_populates="topic", cascade="all, delete-orphan")
    subscriptions: Mapped[List["Subscription"]
                          ] = relationship(back_populates="topic")


# -------------------------------
# SUBSCRIPTION MODEL
# -------------------------------
class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        UniqueConstraint("user_id", "topic_id", name="uq_user_topic"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False)
    topic_id: Mapped[int] = mapped_column(ForeignKey(
        "topics.id", ondelete="CASCADE"), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="subscriptions")
    topic: Mapped["Topic"] = relationship(back_populates="subscriptions")


# -------------------------------
# TIP MODEL
# -------------------------------
class Tip(Base):
    __tablename__ = "tips"
    __table_args__ = (
        Index("ix_tips_topic_created", "topic_id", "created_at"),
        UniqueConstraint("fingerprint", name="uq_tip_fingerprint"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey(
        "topics.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(1024))
    fingerprint: Mapped[Optional[str]] = mapped_column(
        String(64), index=True)  # Used for deduplication
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    topic: Mapped["Topic"] = relationship(back_populates="tips")
    deliveries: Mapped[List["Delivery"]] = relationship(
        back_populates="tip", cascade="all, delete-orphan")


# -------------------------------
# DELIVERY MODEL
# -------------------------------
class Delivery(Base):
    __tablename__ = "deliveries"
    __table_args__ = (
        UniqueConstraint("tip_id", "user_id", name="uq_delivery_tip_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tip_id: Mapped[int] = mapped_column(ForeignKey(
        "tips.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False)
    delivered_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False)
    channel: Mapped[str] = mapped_column(
        String(20), default="app")  # app | push | email
    status: Mapped[str] = mapped_column(
        String(20), default="sent")  # sent | read | failed

    # Relationships
    tip: Mapped["Tip"] = relationship(back_populates="deliveries")
    user: Mapped["User"] = relationship(back_populates="deliveries")
