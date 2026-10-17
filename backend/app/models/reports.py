"""
SQLAlchemy models: reports, reviews.

Bible section 4.5.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import FindingStatus, ReportStatus, ReviewDecision, Severity


class Report(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "reports"

    investigation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    hospital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, server_default=text("1"), nullable=False)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, name="report_status"), server_default="draft", nullable=False
    )
    summary: Mapped[dict] = mapped_column(JSONB, nullable=False)
    storage_key: Mapped[str | None] = mapped_column(Text)
    generated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    signed_off_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    signed_off_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Review(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "reviews"

    finding_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    decision: Mapped[ReviewDecision] = mapped_column(
        Enum(ReviewDecision, name="review_decision"), nullable=False
    )
    comment: Mapped[str | None] = mapped_column(Text)
    edited_severity: Mapped[Severity | None] = mapped_column(Enum(Severity, name="severity"))
    edited_status: Mapped[FindingStatus | None] = mapped_column(
        Enum(FindingStatus, name="finding_status")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
