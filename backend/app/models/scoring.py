"""
SQLAlchemy models: dimension_scores, integration_checks, integration_blueprints.

Bible section 4.5.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    Numeric,
    PrimaryKeyConstraint,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import CompatStatus, Confidence, Dimension


class DimensionScore(Base):
    """Per-dimension computed trust score. Composite PK (investigation_id, dimension)."""

    __tablename__ = "dimension_scores"
    __table_args__ = (
        PrimaryKeyConstraint("investigation_id", "dimension"),
    )

    investigation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    dimension: Mapped[Dimension] = mapped_column(Enum(Dimension, name="dimension"), nullable=False)
    score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    weight: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IntegrationCheck(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "integration_checks"

    investigation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    hospital_system_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    requirement: Mapped[str] = mapped_column(Text, nullable=False)
    vendor_capability: Mapped[str | None] = mapped_column(Text)
    status: Mapped[CompatStatus] = mapped_column(
        Enum(CompatStatus, name="compat_status"), nullable=False
    )
    gap_description: Mapped[str | None] = mapped_column(Text)
    effort: Mapped[str | None] = mapped_column(Text)  # low | medium | high
    recommendation: Mapped[str | None] = mapped_column(Text)
    evidence_ids: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    evidence_confidence: Mapped[Confidence] = mapped_column(
        Enum(Confidence, name="confidence"), server_default="medium", nullable=False
    )


class IntegrationBlueprint(Base):
    """One blueprint per investigation. PK is investigation_id."""

    __tablename__ = "integration_blueprints"

    investigation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    readiness_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    phases: Mapped[dict] = mapped_column(JSONB, nullable=False)
    risks: Mapped[dict | None] = mapped_column(JSONB)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
