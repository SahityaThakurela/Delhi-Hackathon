import uuid
from datetime import date
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Text,
    Integer,
    SmallInteger,
    BigInteger,
    Boolean,
    Date,
    CheckConstraint,
    ForeignKey,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, CreatedAtMixin
from app.models.enums import (
    UserRole,
    user_role_enum,
    SystemCategory,
    system_category_enum,
    DeploymentModel,
    deployment_model_enum,
    RiskAppetite,
    risk_appetite_enum,
    Dimension,
    dimension_enum,
    Severity,
    severity_enum,
)


class Hospital(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "hospitals"

    name: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    state: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hospital_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bed_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    nabh_accredited: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"), nullable=False)
    abdm_maturity: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    risk_appetite: Mapped[RiskAppetite] = mapped_column(
        risk_appetite_enum,
        default=RiskAppetite.balanced,
        server_default=text("'balanced'"),
        nullable=False,
    )
    annual_it_budget_inr: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    data_residency: Mapped[str] = mapped_column(Text, default="india_only", server_default=text("'india_only'"), nullable=False)

    __table_args__ = (
        CheckConstraint("abdm_maturity BETWEEN 0 AND 5", name="check_abdm_maturity_range"),
    )

    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="hospital", cascade="all, delete-orphan")
    systems: Mapped[List["HospitalSystem"]] = relationship("HospitalSystem", back_populates="hospital", cascade="all, delete-orphan")
    requirements: Mapped[List["HospitalRequirement"]] = relationship("HospitalRequirement", back_populates="hospital", cascade="all, delete-orphan")


class User(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "users"

    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        user_role_enum,
        default=UserRole.procurement,
        server_default=text("'procurement'"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"), nullable=False)

    # Relationships
    hospital: Mapped["Hospital"] = relationship("Hospital", back_populates="users")


class HospitalSystem(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "hospital_systems"

    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False,
    )
    category: Mapped[SystemCategory] = mapped_column(system_category_enum, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    vendor_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    standards: Mapped[List[str]] = mapped_column(
        ARRAY(Text),
        default=list,
        server_default=text("'{}'::text[]"),
        nullable=False,
    )
    interfaces: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        server_default=text("'{}'::jsonb"),
        nullable=False,
    )
    deployment: Mapped[Optional[DeploymentModel]] = mapped_column(deployment_model_enum, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    hospital: Mapped["Hospital"] = relationship("Hospital", back_populates="systems")


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
