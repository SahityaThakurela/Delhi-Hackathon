import uuid
from typing import Optional, List
from sqlalchemy import (
    Text,
    ForeignKey,
    text,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDPrimaryKeyMixin, TimestampMixin, CreatedAtMixin
from app.models.enums import (
    SystemCategory,
    system_category_enum,
    DeploymentModel,
    deployment_model_enum,
)


class Vendor(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "vendors"

    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    website: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    country: Mapped[str] = mapped_column(Text, default="India", server_default=text("'India'"), nullable=False)
    cin: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contact_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    products: Mapped[List["Product"]] = relationship("Product", back_populates="vendor", cascade="all, delete-orphan")


class Product(Base, UUIDPrimaryKeyMixin, CreatedAtMixin):
    __tablename__ = "products"

    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vendors.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[SystemCategory] = mapped_column(system_category_enum, nullable=False)
    version: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deployment_models: Mapped[List[DeploymentModel]] = mapped_column(
        ARRAY(deployment_model_enum),
        default=list,
        server_default=text("'{}'::deployment_model[]"),
        nullable=False,
    )
    claimed_standards: Mapped[List[str]] = mapped_column(
        ARRAY(Text),
        default=list,
        server_default=text("'{}'::text[]"),
        nullable=False,
    )
    claimed_certifications: Mapped[List[str]] = mapped_column(
        ARRAY(Text),
        default=list,
        server_default=text("'{}'::text[]"),
        nullable=False,
    )

    # Relationships
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="products")
