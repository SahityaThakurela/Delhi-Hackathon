import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from sqlalchemy import (
    Text,
    Numeric,
    DateTime,
    ForeignKey,
    CheckConstraint,
    text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import (
    Dimension,
    dimension_enum,
    CompatStatus,
    compat_status_enum,
    Confidence,
    confidence_enum,
)


class DimensionScore(Base):
    __tablename__ = "dimension_scores"

    investigation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    dimension: Mapped[Dimension] = mapped_column(
        dimension_enum,
        primary_key=True,
    )
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        nullable=False,
    )


class IntegrationCheck(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "integration_checks"

    investigation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
    )
    hospital_system_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hospital_systems.id"),
        nullable=True,
    )
    requirement: Mapped[str] = mapped_column(Text, nullable=False)
    vendor_capability: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[CompatStatus] = mapped_column(compat_status_enum, nullable=False)
    gap_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    effort: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence_ids: Mapped[List[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        default=list,
        server_default=text("'{}'::uuid[]"),
        nullable=False,
    )
    evidence_confidence: Mapped[Confidence] = mapped_column(
        confidence_enum,
        default=Confidence.medium,
        server_default=text("'medium'"),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("effort IN ('low','medium','high')", name="check_integration_check_effort"),
    )


class IntegrationBlueprint(Base):
    __tablename__ = "integration_blueprints"

    investigation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    readiness_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    phases: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    risks: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        nullable=False,
    )
