import uuid
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Text,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDPrimaryKeyMixin, CreatedAtMixin
from app.models.enums import (
    Dimension,
    dimension_enum,
    Severity,
    severity_enum,
)


class RequirementCatalogue(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "requirement_catalogue"

    code: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    dimension: Mapped[Dimension] = mapped_column(dimension_enum, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    authority: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    applies_to: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )
    check_type: Mapped[str] = mapped_column(Text, default="evidence", server_default=text("'evidence'"), nullable=False)
    rule: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )
    default_severity: Mapped[Severity] = mapped_column(
        severity_enum,
        default=Severity.medium,
        server_default=text("'medium'"),
        nullable=False,
    )

    hospital_requirements: Mapped[List["HospitalRequirement"]] = relationship(
        "HospitalRequirement",
        back_populates="catalogue",
    )


class HospitalRequirement(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "hospital_requirements"

    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False,
    )
    catalogue_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("requirement_catalogue.id"),
        nullable=True,
    )
    dimension: Mapped[Dimension] = mapped_column(dimension_enum, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mandatory: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)
    severity_if_unmet: Mapped[Severity] = mapped_column(
        severity_enum,
        default=Severity.high,
        server_default=text("'high'"),
        nullable=False,
    )
    rule: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )
    is_custom: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)

    # Relationships
    hospital: Mapped["Hospital"] = relationship("Hospital", back_populates="requirements")
    catalogue: Mapped[Optional["RequirementCatalogue"]] = relationship("RequirementCatalogue", back_populates="hospital_requirements")
