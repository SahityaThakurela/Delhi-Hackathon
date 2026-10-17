"""
SQLAlchemy models: requirement_catalogue, hospital_requirements.

Bible section 4.2 (continued).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import Dimension, Severity


class RequirementCatalogue(UUIDPrimaryKeyMixin, Base):
    """Global requirement catalogue curated by the KYRO team – hospital-agnostic."""

    __tablename__ = "requirement_catalogue"

    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    dimension: Mapped[Dimension] = mapped_column(
        Enum(Dimension, name="dimension"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    authority: Mapped[str | None] = mapped_column(Text)
    reference_url: Mapped[str | None] = mapped_column(Text)
    reference_date: Mapped[date | None] = mapped_column(Date)
    applies_to: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    check_type: Mapped[str] = mapped_column(Text, server_default="evidence", nullable=False)
    rule: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    default_severity: Mapped[Severity] = mapped_column(
        Enum(Severity, name="severity"),
        server_default="medium",
        nullable=False,
    )

    # relationships
    hospital_requirements: Mapped[list["HospitalRequirement"]] = relationship(
        "HospitalRequirement", back_populates="catalogue_item"
    )


class HospitalRequirement(UUIDPrimaryKeyMixin, Base):
    """Per-hospital active checklist row (imported from catalogue or custom)."""

    __tablename__ = "hospital_requirements"

    hospital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    catalogue_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    dimension: Mapped[Dimension] = mapped_column(
        Enum(Dimension, name="dimension"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    mandatory: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    severity_if_unmet: Mapped[Severity] = mapped_column(
        Enum(Severity, name="severity"), server_default="high", nullable=False
    )
    rule: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    is_custom: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # relationships
    catalogue_item: Mapped["RequirementCatalogue | None"] = relationship(
        "RequirementCatalogue", back_populates="hospital_requirements",
        foreign_keys=[catalogue_id],
    )
