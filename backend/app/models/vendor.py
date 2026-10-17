"""
SQLAlchemy models: vendors, products.

Bible section 4.3.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Text, func, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import DeploymentModel, SystemCategory


class Vendor(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "vendors"

    hospital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    website: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str] = mapped_column(Text, server_default="India", nullable=False)
    cin: Mapped[str | None] = mapped_column(Text)  # MCA corporate identity number
    contact_name: Mapped[str | None] = mapped_column(Text)
    contact_email: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # relationships
    products: Mapped[list["Product"]] = relationship(
        "Product", back_populates="vendor", passive_deletes=True
    )


class Product(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "products"

    vendor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[SystemCategory] = mapped_column(
        Enum(SystemCategory, name="system_category"), nullable=False
    )
    version: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    deployment_models: Mapped[list] = mapped_column(
        JSONB, server_default=text("'[]'::jsonb")  # stored as jsonb array of deployment_model strings
    )
    claimed_standards: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    claimed_certifications: Mapped[list] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # relationships
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="products", foreign_keys=[vendor_id])
