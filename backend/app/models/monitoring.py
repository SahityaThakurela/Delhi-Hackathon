"""
SQLAlchemy models: monitoring_watches, alerts.

Bible section 4.5.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import AlertStatus, Severity


class MonitoringWatch(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "monitoring_watches"

    hospital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    watch_type: Mapped[str] = mapped_column(Text, nullable=False)
    # watch_type values: certificate_expiry | cve | regulatory | document_change
    config: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Alert(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "alerts"

    hospital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    watch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    severity: Mapped[Severity] = mapped_column(Enum(Severity, name="severity"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    detail: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[AlertStatus] = mapped_column(
        Enum(AlertStatus, name="alert_status"), server_default="new", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
