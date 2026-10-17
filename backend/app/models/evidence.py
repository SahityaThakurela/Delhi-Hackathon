"""
SQLAlchemy models: evidence, findings, finding_evidence (join table), debate_messages.

Bible section 4.4 (continued).
"""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import (
    AgentName,
    ClaimOrigin,
    Confidence,
    DebateRole,
    Dimension,
    EvidenceSource,
    FindingStatus,
    ReviewDecision,
    Severity,
)


class Evidence(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "evidence"

    hospital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    investigation_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    vendor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    source_type: Mapped[EvidenceSource] = mapped_column(
        Enum(EvidenceSource, name="evidence_source"), nullable=False
    )
    source_name: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    page: Mapped[int | None] = mapped_column(Integer)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    doc_version: Mapped[str | None] = mapped_column(Text)
    source_date: Mapped[date | None] = mapped_column(Date)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_independent: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    reliability: Mapped[Confidence] = mapped_column(
        Enum(Confidence, name="confidence"), server_default="medium", nullable=False
    )
    content_hash: Mapped[str | None] = mapped_column(Text)


class Finding(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "findings"

    investigation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    hospital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    agent: Mapped[AgentName] = mapped_column(Enum(AgentName, name="agent_name"), nullable=False)
    dimension: Mapped[Dimension] = mapped_column(Enum(Dimension, name="dimension"), nullable=False)
    requirement_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[FindingStatus] = mapped_column(
        Enum(FindingStatus, name="finding_status"), nullable=False
    )
    severity: Mapped[Severity] = mapped_column(
        Enum(Severity, name="severity"), nullable=False
    )
    evidence_confidence: Mapped[Confidence] = mapped_column(
        Enum(Confidence, name="confidence"), nullable=False
    )
    claim_origin: Mapped[ClaimOrigin] = mapped_column(
        Enum(ClaimOrigin, name="claim_origin"), nullable=False
    )
    recommended_action: Mapped[str | None] = mapped_column(Text)
    missing_evidence: Mapped[str | None] = mapped_column(Text)
    review_decision: Mapped[ReviewDecision] = mapped_column(
        Enum(ReviewDecision, name="review_decision"),
        server_default="pending",
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # relationships
    finding_evidence: Mapped[list["FindingEvidence"]] = relationship(
        "FindingEvidence", back_populates="finding", passive_deletes=True
    )


class FindingEvidence(Base):
    """Association table: many-many between findings and evidence with a relation label."""

    __tablename__ = "finding_evidence"
    __table_args__ = (
        PrimaryKeyConstraint("finding_id", "evidence_id"),
    )

    finding_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    evidence_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    relation: Mapped[str | None] = mapped_column(Text)  # supports | contradicts | context

    # relationships
    finding: Mapped["Finding"] = relationship(
        "Finding", back_populates="finding_evidence", foreign_keys=[finding_id]
    )
    evidence: Mapped["Evidence"] = relationship(
        "Evidence", foreign_keys=[evidence_id]
    )


class DebateMessage(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "debate_messages"

    investigation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    finding_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    agent: Mapped[AgentName] = mapped_column(Enum(AgentName, name="agent_name"), nullable=False)
    role: Mapped[DebateRole] = mapped_column(Enum(DebateRole, name="debate_role"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_ids: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
