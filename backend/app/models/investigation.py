"""
SQLAlchemy models: investigations, agent_runs, timeline_events, steering_commands.

Bible section 4.4.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import AgentName, Dimension, InvStatus, RunStatus, Severity


class Investigation(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "investigations"

    hospital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    vendor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    title: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[InvStatus] = mapped_column(
        Enum(InvStatus, name="inv_status"), server_default="draft", nullable=False
    )
    # dimensions stored as jsonb array of dimension enum strings
    dimensions: Mapped[list] = mapped_column(JSONB, nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text)
    overall_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    score_confidence: Mapped[float | None] = mapped_column(Numeric(4, 3))
    overall_risk: Mapped[Severity | None] = mapped_column(
        Enum(Severity, name="severity")
    )
    summary: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # relationships
    agent_runs: Mapped[list["AgentRun"]] = relationship(
        "AgentRun", back_populates="investigation", passive_deletes=True
    )
    timeline_events: Mapped[list["TimelineEvent"]] = relationship(
        "TimelineEvent", back_populates="investigation", passive_deletes=True
    )
    steering_commands: Mapped[list["SteeringCommand"]] = relationship(
        "SteeringCommand", back_populates="investigation", passive_deletes=True
    )


class AgentRun(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "agent_runs"

    investigation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    agent: Mapped[AgentName] = mapped_column(
        Enum(AgentName, name="agent_name"), nullable=False
    )
    status: Mapped[RunStatus] = mapped_column(
        Enum(RunStatus, name="run_status"), server_default="pending", nullable=False
    )
    progress: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"))
    current_task: Mapped[str | None] = mapped_column(Text)
    output: Mapped[dict | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)
    token_usage: Mapped[dict | None] = mapped_column(JSONB)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # relationships
    investigation: Mapped["Investigation"] = relationship(
        "Investigation", back_populates="agent_runs", foreign_keys=[investigation_id]
    )


class TimelineEvent(Base):
    """Powers 'replay the timeline' feature. Uses bigserial PK for ordering."""

    __tablename__ = "timeline_events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    investigation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    event: Mapped[str] = mapped_column(Text, nullable=False)
    agent: Mapped[AgentName | None] = mapped_column(Enum(AgentName, name="agent_name"))
    payload: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # relationships
    investigation: Mapped["Investigation"] = relationship(
        "Investigation", back_populates="timeline_events", foreign_keys=[investigation_id]
    )


class SteeringCommand(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "steering_commands"

    investigation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    instruction: Mapped[str] = mapped_column(Text, nullable=False)
    parsed: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(Text, server_default="received", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # relationships
    investigation: Mapped["Investigation"] = relationship(
        "Investigation", back_populates="steering_commands", foreign_keys=[investigation_id]
    )
