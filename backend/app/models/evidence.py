import uuid
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Text,
    Integer,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    CheckConstraint,
    text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDPrimaryKeyMixin, CreatedAtMixin
from app.models.enums import (
    EvidenceSource,
    evidence_source_enum,
    Confidence,
    confidence_enum,
    AgentName,
    agent_name_enum,
    Dimension,
    dimension_enum,
    FindingStatus,
    finding_status_enum,
    Severity,
    severity_enum,
    ClaimOrigin,
    claim_origin_enum,
    ReviewDecision,
    review_decision_enum,
    DebateRole,
    debate_role_enum,
)


class Evidence(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "evidence"

    hospital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    investigation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=True,
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
    source_type: Mapped[EvidenceSource] = mapped_column(evidence_source_enum, nullable=False)
    source_name: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=True,
    )
    chunk_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_chunks.id"),
        nullable=True,
    )
    page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    doc_version: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    retrieved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=func.now(),
        server_default=func.now(),
        nullable=False,
    )
    is_independent: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    reliability: Mapped[Confidence] = mapped_column(
        confidence_enum,
        default=Confidence.medium,
        server_default=text("'medium'"),
        nullable=False,
    )
    content_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("evidence_investigation_id_idx", "investigation_id"),
    )


class Finding(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "findings"

    investigation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
    )
    hospital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    agent: Mapped[AgentName] = mapped_column(agent_name_enum, nullable=False)
    dimension: Mapped[Dimension] = mapped_column(dimension_enum, nullable=False)
    requirement_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hospital_requirements.id"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[FindingStatus] = mapped_column(finding_status_enum, nullable=False)
    severity: Mapped[Severity] = mapped_column(severity_enum, nullable=False)
    evidence_confidence: Mapped[Confidence] = mapped_column(confidence_enum, nullable=False)
    claim_origin: Mapped[ClaimOrigin] = mapped_column(claim_origin_enum, nullable=False)
    recommended_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    missing_evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_decision: Mapped[ReviewDecision] = mapped_column(
        review_decision_enum,
        default=ReviewDecision.pending,
        server_default=text("'pending'"),
        nullable=False,
    )

    __table_args__ = (
        Index("findings_investigation_id_dimension_idx", "investigation_id", "dimension"),
    )

    finding_evidences: Mapped[List["FindingEvidence"]] = relationship(
        "FindingEvidence",
        back_populates="finding",
        cascade="all, delete-orphan",
    )


class FindingEvidence(Base):
    __tablename__ = "finding_evidence"

    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("findings.id", ondelete="CASCADE"),
        primary_key=True,
    )
    evidence_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("evidence.id", ondelete="CASCADE"),
        primary_key=True,
    )
    relation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("relation IN ('supports','contradicts','context')", name="check_finding_evidence_relation"),
    )

    finding: Mapped["Finding"] = relationship("Finding", back_populates="finding_evidences")
    evidence: Mapped["Evidence"] = relationship("Evidence")


class DebateMessage(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "debate_messages"

    investigation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
    )
    finding_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("findings.id", ondelete="SET NULL"),
        nullable=True,
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    agent: Mapped[AgentName] = mapped_column(agent_name_enum, nullable=False)
    role: Mapped[DebateRole] = mapped_column(debate_role_enum, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_ids: Mapped[List[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        default=list,
        server_default=text("'{}'::uuid[]"),
        nullable=False,
    )
