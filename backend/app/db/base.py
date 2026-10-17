"""
SQLAlchemy 2.0 declarative base plus reusable column mixins.

Mixins
------
UUIDPrimaryKeyMixin  – adds ``id uuid PK DEFAULT gen_random_uuid()``
TimestampMixin       – adds ``created_at`` and ``updated_at`` (auto-set / auto-updated)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Shared declarative base for all KYRO models."""
    pass


class UUIDPrimaryKeyMixin:
    """Adds ``id`` uuid primary key generated server-side by pgcrypto gen_random_uuid()."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )


class TimestampMixin:
    """Adds ``created_at`` and ``updated_at`` timestamps managed by the DB."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
