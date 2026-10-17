import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from sqlalchemy import (
    Text,
    Numeric,
    SmallInteger,
    BigInteger,
    ForeignKey,
    DateTime,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDPrimaryKeyMixin, CreatedAtMixin
from app.models.enums import (
    InvStatus,
    inv_status_enum,
    Dimension,
    dimension_enum,
    Severity,
    severity_enum,
    AgentName,
    agent_name_enum,
    RunStatus,
    run_status_enum,
)


class Investigation(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "investigations"

    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False,
    )
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendors.id"),
        nullable=False,
    )
    product_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id"),
        nullable=True,
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[InvStatus] = mapped_column(
        inv_status_enum,
        default=InvStatus.draft,
        server_default=text("'draft'"),
        nullable=False,
    )
    dimensions: Mapped[List[Dimension]] = mapped_column(
        ARRAY(dimension_enum),
        nullable=False,
    )
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    overall_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    score_confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 3), nullable=True)
    overall_risk: Mapped[Optional[Severity]] = mapped_column(severity_enum, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    agent_runs: Mapped[List["AgentRun"]] = relationship("AgentRun", back_populates="investigation", cascade="all, delete-orphan")
    timeline_events: Mapped[List["TimelineEvent"]] = relationship("TimelineEvent", back_populates="investigation", cascade="all, delete-orphan")
    steering_commands: Mapped[List["SteeringCommand"]] = relationship("SteeringCommand", back_populates="investigation", cascade="all, delete-orphan")


class AgentRun(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "agent_runs"

    investigation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent: Mapped[AgentName] = mapped_column(agent_name_enum, nullable=False)
    status: Mapped[RunStatus] = mapped_column(
        run_status_enum,
        default=RunStatus.pending,
        server_default=text("'pending'"),
        nullable=False,
    )
    progress: Mapped[int] = mapped_column(
        SmallInteger,
        default=0,
        server_default=text("0"),
        nullable=False,
    )
    current_task: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_usage: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    investigation: Mapped["Investigation"] = relationship("Investigation", back_populates="agent_runs")


class SteeringCommand(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "steering_commands"

    investigation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    instruction: Mapped[str] = mapped_column(Text, nullable=False)
    parsed: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(Text, default="received", server_default=text("'received'"), nullable=False)

    # Relationships
    investigation: Mapped["Investigation"] = relationship("Investigation", back_populates="steering_commands")


class TimelineEvent(Base, CreatedAtMixin):
    __tablename__ = "timeline_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("investigations.id", ondelete="CASCADE"),
        nullable=False,
    )
    event: Mapped[str] = mapped_column(Text, nullable=False)
    agent: Mapped[Optional[AgentName]] = mapped_column(agent_name_enum, nullable=True)
    payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    # Relationships
    investigation: Mapped["Investigation"] = relationship("Investigation", back_populates="timeline_events")
