"""
SQLAlchemy models: documents, document_chunks.

document_chunks carries a pgvector Vector(1536) embedding column with an
HNSW cosine index (created in the Alembic migration).

Bible section 4.3.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Enum, Integer, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDPrimaryKeyMixin
from app.models.enums import DocStatus

try:
    from pgvector.sqlalchemy import Vector
    _VECTOR_TYPE = Vector(1536)
except ImportError:  # fallback so linters don't fail without pgvector installed
    from sqlalchemy import Text as _Vector
    _VECTOR_TYPE = None  # type: ignore[assignment]


class Document(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "documents"

    hospital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    vendor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    product_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    doc_type: Mapped[str] = mapped_column(Text, nullable=False)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str | None] = mapped_column(Text)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    sha256: Mapped[str | None] = mapped_column(Text)
    version_label: Mapped[str | None] = mapped_column(Text)
    doc_date: Mapped[date | None] = mapped_column(Date)
    valid_until: Mapped[date | None] = mapped_column(Date)
    status: Mapped[DocStatus] = mapped_column(
        Enum(DocStatus, name="doc_status"),
        server_default="uploaded",
        nullable=False,
    )
    error: Mapped[str | None] = mapped_column(Text)
    page_count: Mapped[int | None] = mapped_column(Integer)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # relationships
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk", back_populates="document", passive_deletes=True
    )


class DocumentChunk(UUIDPrimaryKeyMixin, Base):
    """
    A chunk of a document with a 1536-dimensional embedding vector.

    The HNSW cosine index is created in the Alembic migration:
        CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);
    """

    __tablename__ = "document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    hospital_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page: Mapped[int | None] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int | None] = mapped_column(Integer)

    if _VECTOR_TYPE is not None:
        embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))

    # relationships
    document: Mapped["Document"] = relationship(
        "Document", back_populates="chunks", foreign_keys=[document_id]
    )
