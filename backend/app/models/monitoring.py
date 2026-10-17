import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    CheckConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDPrimaryKeyMixin, CreatedAtMixin
from app.models.enums import (
    Severity,
    severity_enum,
    AlertStatus,
    alert_status_enum,
)


class MonitoringWatch(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "monitoring_watches"

    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False,
    )
    vendor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendors.id"),
        nullable=True,
    )
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id"),
        nullable=True,
    )
    watch_type: Mapped[str] = mapped_column(Text, nullable=False)
    config: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "watch_type IN ('certificate_expiry','cve','regulatory','document_change')",
            name="check_monitoring_watch_type",
        ),
    )


class Alert(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "alerts"

    hospital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    watch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("monitoring_watches.id", ondelete="SET NULL"),
        nullable=True,
    )
    vendor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendors.id"),
        nullable=True,
    )
    severity: Mapped[Severity] = mapped_column(severity_enum, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[AlertStatus] = mapped_column(
        alert_status_enum,
        default=AlertStatus.new,
        server_default=text("'new'"),
        nullable=False,
    )
