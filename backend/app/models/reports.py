import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Text,
    Integer,
    DateTime,
    ForeignKey,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDPrimaryKeyMixin, CreatedAtMixin
from app.models.enums import (
    ReportStatus,
    report_status_enum,
    ReviewDecision,
    review_decision_enum,
    Severity,
    severity_enum,
    FindingStatus,
    finding_status_enum,
)


class Report(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "reports"

    investigation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
    )
    hospital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default=text("1"), nullable=False)
    status: Mapped[ReportStatus] = mapped_column(
        report_status_enum,
        default=ReportStatus.draft,
        server_default=text("'draft'"),
        nullable=False,
    )
    summary: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    storage_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    signed_off_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    signed_off_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class Review(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "reviews"

    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("findings.id", ondelete="CASCADE"),
        nullable=False,
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    decision: Mapped[ReviewDecision] = mapped_column(review_decision_enum, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    edited_severity: Mapped[Optional[Severity]] = mapped_column(severity_enum, nullable=True)
    edited_status: Mapped[Optional[FindingStatus]] = mapped_column(finding_status_enum, nullable=True)
