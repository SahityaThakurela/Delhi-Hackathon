"""
SQLAlchemy models: hospitals, users, hospital_systems.

Bible section 4.2 – Tenancy, profile and requirements.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import DeploymentModel, RiskAppetite, SystemCategory, UserRole


class Hospital(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "hospitals"

    name: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str | None] = mapped_column(Text)
    state: Mapped[str | None] = mapped_column(Text)
    hospital_type: Mapped[str | None] = mapped_column(Text)
    bed_count: Mapped[int | None] = mapped_column(Integer)
    nabh_accredited: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    abdm_maturity: Mapped[int | None] = mapped_column(SmallInteger)
    risk_appetite: Mapped[RiskAppetite] = mapped_column(
        Enum(RiskAppetite, name="risk_appetite"),
        server_default="balanced",
        nullable=False,
    )
    annual_it_budget_inr: Mapped[int | None] = mapped_column(BigInteger)
    data_residency: Mapped[str] = mapped_column(Text, server_default="india_only", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="hospital", passive_deletes=True)
    hospital_systems: Mapped[list["HospitalSystem"]] = relationship("HospitalSystem", back_populates="hospital", passive_deletes=True)


class User(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "users"

    hospital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        nullable=False,
        server_default="procurement",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # relationships
    hospital: Mapped["Hospital"] = relationship("Hospital", back_populates="users", foreign_keys=[hospital_id])


class HospitalSystem(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "hospital_systems"

    hospital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    category: Mapped[SystemCategory] = mapped_column(
        Enum(SystemCategory, name="system_category"), nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    vendor_name: Mapped[str | None] = mapped_column(Text)
    version: Mapped[str | None] = mapped_column(Text)
    standards: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))  # text[]
    interfaces: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    deployment: Mapped[DeploymentModel | None] = mapped_column(
        Enum(DeploymentModel, name="deployment_model")
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # relationships
    hospital: Mapped["Hospital"] = relationship("Hospital", back_populates="hospital_systems", foreign_keys=[hospital_id])
