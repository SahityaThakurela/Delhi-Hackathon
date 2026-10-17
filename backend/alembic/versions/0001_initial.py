"""Initial database schema and extensions

Revision ID: 0001_initial
Revises: 
Create Date: 2026-10-17 13:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ENUMS = [
    ("user_role", ("admin", "procurement", "it", "security", "clinical", "reviewer")),
    ("system_category", ("his_emr", "lis", "pacs", "ris", "erp", "billing", "abdm_gateway", "other")),
    ("deployment_model", ("on_prem", "private_cloud", "public_cloud", "hybrid", "saas")),
    ("risk_appetite", ("conservative", "balanced", "aggressive")),
    ("dimension", ("compliance", "security_privacy", "clinical", "financial", "integration", "operations")),
    ("agent_name", ("orchestrator", "compliance", "clinical_evidence", "security_privacy", "financial", "integration_fit", "operations", "skeptic")),
    ("finding_status", ("supported", "partially_supported", "contradictory", "unverified", "insufficient_evidence", "not_applicable")),
    ("severity", ("critical", "high", "medium", "low", "info")),
    ("confidence", ("high", "medium", "low")),
    ("claim_origin", ("vendor_claim", "independently_verified", "inferred")),
    ("inv_status", ("draft", "queued", "running", "paused", "completed", "failed", "cancelled")),
    ("run_status", ("pending", "running", "completed", "failed", "skipped")),
    ("review_decision", ("pending", "accepted", "rejected", "edited")),
    ("compat_status", ("compatible", "partial", "incompatible", "unknown")),
    ("evidence_source", ("vendor_document", "government_portal", "standard", "research", "public_web", "hospital_data", "catalogue")),
    ("doc_status", ("uploaded", "processing", "processed", "failed")),
    ("report_status", ("draft", "in_review", "final")),
    ("alert_status", ("new", "acknowledged", "dismissed")),
    ("debate_role", ("claim", "challenge", "rebuttal", "resolution")),
]


def upgrade() -> None:
    # 1. Extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    # 2. Native PostgreSQL Enums
    for enum_name, enum_values in ENUMS:
        values_sql = ", ".join(f"'{v}'" for v in enum_values)
        op.execute(f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{enum_name}') THEN CREATE TYPE {enum_name} AS ENUM ({values_sql}); END IF; END $$;")

    # 3. Hospitals
    op.create_table(
        "hospitals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("city", sa.Text(), nullable=True),
        sa.Column("state", sa.Text(), nullable=True),
        sa.Column("hospital_type", sa.Text(), nullable=True),
        sa.Column("bed_count", sa.Integer(), nullable=True),
        sa.Column("nabh_accredited", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("abdm_maturity", sa.SmallInteger(), nullable=True),
        sa.Column("risk_appetite", postgresql.ENUM(name="risk_appetite", create_type=False), server_default=sa.text("'balanced'"), nullable=False),
        sa.Column("annual_it_budget_inr", sa.BigInteger(), nullable=True),
        sa.Column("data_residency", sa.Text(), server_default=sa.text("'india_only'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("abdm_maturity BETWEEN 0 AND 5", name="check_abdm_maturity_range"),
    )

    # 4. Users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.Text(), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("role", postgresql.ENUM(name="user_role", create_type=False), server_default=sa.text("'procurement'"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 5. Hospital Systems
    op.create_table(
        "hospital_systems",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", postgresql.ENUM(name="system_category", create_type=False), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("vendor_name", sa.Text(), nullable=True),
        sa.Column("version", sa.Text(), nullable=True),
        sa.Column("standards", postgresql.ARRAY(sa.Text()), server_default=sa.text("'{}'::text[]"), nullable=False),
        sa.Column("interfaces", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("deployment", postgresql.ENUM(name="deployment_model", create_type=False), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 6. Requirement Catalogue
    op.create_table(
        "requirement_catalogue",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.Text(), nullable=False, unique=True),
        sa.Column("dimension", postgresql.ENUM(name="dimension", create_type=False), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("authority", sa.Text(), nullable=True),
        sa.Column("reference_url", sa.Text(), nullable=True),
        sa.Column("reference_date", sa.Date(), nullable=True),
        sa.Column("applies_to", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("check_type", sa.Text(), server_default=sa.text("'evidence'"), nullable=False),
        sa.Column("rule", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("default_severity", postgresql.ENUM(name="severity", create_type=False), server_default=sa.text("'medium'"), nullable=False),
    )

    # 7. Hospital Requirements
    op.create_table(
        "hospital_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("catalogue_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("requirement_catalogue.id"), nullable=True),
        sa.Column("dimension", postgresql.ENUM(name="dimension", create_type=False), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("mandatory", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("severity_if_unmet", postgresql.ENUM(name="severity", create_type=False), server_default=sa.text("'high'"), nullable=False),
        sa.Column("rule", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("is_custom", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 8. Vendors
    op.create_table(
        "vendors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("website", sa.Text(), nullable=True),
        sa.Column("country", sa.Text(), server_default=sa.text("'India'"), nullable=False),
        sa.Column("cin", sa.Text(), nullable=True),
        sa.Column("contact_name", sa.Text(), nullable=True),
        sa.Column("contact_email", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 9. Products
    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("category", postgresql.ENUM(name="system_category", create_type=False), nullable=False),
        sa.Column("version", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("deployment_models", postgresql.ARRAY(postgresql.ENUM(name="deployment_model", create_type=False)), server_default=sa.text("'{}'::deployment_model[]"), nullable=False),
        sa.Column("claimed_standards", postgresql.ARRAY(sa.Text()), server_default=sa.text("'{}'::text[]"), nullable=False),
        sa.Column("claimed_certifications", postgresql.ARRAY(sa.Text()), server_default=sa.text("'{}'::text[]"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 10. Documents
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="SET NULL"), nullable=True),
        sa.Column("doc_type", sa.Text(), nullable=False),
        sa.Column("filename", sa.Text(), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("mime_type", sa.Text(), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("sha256", sa.Text(), nullable=True),
        sa.Column("version_label", sa.Text(), nullable=True),
        sa.Column("doc_date", sa.Date(), nullable=True),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("status", postgresql.ENUM(name="doc_status", create_type=False), server_default=sa.text("'uploaded'"), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 11. Document Chunks
    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("embedding", Vector(1536), nullable=True),
    )
    op.create_index("document_chunks_document_id_idx", "document_chunks", ["document_id"])
    op.create_index(
        "document_chunks_embedding_hnsw_idx",
        "document_chunks",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )

    # 12. Investigations
    op.create_table(
        "investigations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vendors.id"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("status", postgresql.ENUM(name="inv_status", create_type=False), server_default=sa.text("'draft'"), nullable=False),
        sa.Column("dimensions", postgresql.ARRAY(postgresql.ENUM(name="dimension", create_type=False)), nullable=False),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("overall_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("score_confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("overall_risk", postgresql.ENUM(name="severity", create_type=False), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 13. Agent Runs
    op.create_table(
        "agent_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("investigation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("agent", postgresql.ENUM(name="agent_name", create_type=False), nullable=False),
        sa.Column("status", postgresql.ENUM(name="run_status", create_type=False), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("progress", sa.SmallInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column("current_task", sa.Text(), nullable=True),
        sa.Column("output", postgresql.JSONB(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("token_usage", postgresql.JSONB(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 14. Evidence
    op.create_table(
        "evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("investigation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("investigations.id", ondelete="CASCADE"), nullable=True),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vendors.id"), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("source_type", postgresql.ENUM(name="evidence_source", create_type=False), nullable=False),
        sa.Column("source_name", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documents.id"), nullable=True),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("document_chunks.id"), nullable=True),
        sa.Column("page", sa.Integer(), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("doc_version", sa.Text(), nullable=True),
        sa.Column("source_date", sa.Date(), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_independent", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("reliability", postgresql.ENUM(name="confidence", create_type=False), server_default=sa.text("'medium'"), nullable=False),
        sa.Column("content_hash", sa.Text(), nullable=True),
    )
    op.create_index("evidence_investigation_id_idx", "evidence", ["investigation_id"])

    # 15. Findings
    op.create_table(
        "findings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("investigation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent", postgresql.ENUM(name="agent_name", create_type=False), nullable=False),
        sa.Column("dimension", postgresql.ENUM(name="dimension", create_type=False), nullable=False),
        sa.Column("requirement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hospital_requirements.id"), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", postgresql.ENUM(name="finding_status", create_type=False), nullable=False),
        sa.Column("severity", postgresql.ENUM(name="severity", create_type=False), nullable=False),
        sa.Column("evidence_confidence", postgresql.ENUM(name="confidence", create_type=False), nullable=False),
        sa.Column("claim_origin", postgresql.ENUM(name="claim_origin", create_type=False), nullable=False),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("missing_evidence", sa.Text(), nullable=True),
        sa.Column("review_decision", postgresql.ENUM(name="review_decision", create_type=False), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("findings_investigation_id_dimension_idx", "findings", ["investigation_id", "dimension"])

    # 16. Finding Evidence
    op.create_table(
        "finding_evidence",
        sa.Column("finding_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("findings.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("evidence.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("relation", sa.Text(), nullable=True),
        sa.CheckConstraint("relation IN ('supports','contradicts','context')", name="check_finding_evidence_relation"),
    )

    # 17. Debate Messages
    op.create_table(
        "debate_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("investigation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("finding_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("findings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("agent", postgresql.ENUM(name="agent_name", create_type=False), nullable=False),
        sa.Column("role", postgresql.ENUM(name="debate_role", create_type=False), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("evidence_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), server_default=sa.text("'{}'::uuid[]"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 18. Steering Commands
    op.create_table(
        "steering_commands",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("investigation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("instruction", sa.Text(), nullable=False),
        sa.Column("parsed", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.Text(), server_default=sa.text("'received'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 19. Timeline Events
    op.create_table(
        "timeline_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("investigation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event", sa.Text(), nullable=False),
        sa.Column("agent", postgresql.ENUM(name="agent_name", create_type=False), nullable=True),
        sa.Column("payload", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 20. Dimension Scores
    op.create_table(
        "dimension_scores",
        sa.Column("investigation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("investigations.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("dimension", postgresql.ENUM(name="dimension", create_type=False), primary_key=True),
        sa.Column("score", sa.Numeric(5, 2), nullable=False),
        sa.Column("weight", sa.Numeric(4, 3), nullable=False),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 21. Integration Checks
    op.create_table(
        "integration_checks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("investigation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("hospital_system_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hospital_systems.id"), nullable=True),
        sa.Column("requirement", sa.Text(), nullable=False),
        sa.Column("vendor_capability", sa.Text(), nullable=True),
        sa.Column("status", postgresql.ENUM(name="compat_status", create_type=False), nullable=False),
        sa.Column("gap_description", sa.Text(), nullable=True),
        sa.Column("effort", sa.Text(), nullable=True),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("evidence_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), server_default=sa.text("'{}'::uuid[]"), nullable=False),
        sa.Column("evidence_confidence", postgresql.ENUM(name="confidence", create_type=False), server_default=sa.text("'medium'"), nullable=False),
        sa.CheckConstraint("effort IN ('low','medium','high')", name="check_integration_check_effort"),
    )

    # 22. Integration Blueprints
    op.create_table(
        "integration_blueprints",
        sa.Column("investigation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("investigations.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("readiness_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("phases", postgresql.JSONB(), nullable=False),
        sa.Column("risks", postgresql.JSONB(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 23. Reports
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("investigation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("status", postgresql.ENUM(name="report_status", create_type=False), server_default=sa.text("'draft'"), nullable=False),
        sa.Column("summary", postgresql.JSONB(), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=True),
        sa.Column("generated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("signed_off_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("signed_off_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 24. Reviews
    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("finding_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("findings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("decision", postgresql.ENUM(name="review_decision", create_type=False), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("edited_severity", postgresql.ENUM(name="severity", create_type=False), nullable=True),
        sa.Column("edited_status", postgresql.ENUM(name="finding_status", create_type=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 25. Monitoring Watches
    op.create_table(
        "monitoring_watches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vendors.id"), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id"), nullable=True),
        sa.Column("watch_type", sa.Text(), nullable=False),
        sa.Column("config", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "watch_type IN ('certificate_expiry','cve','regulatory','document_change')",
            name="check_monitoring_watch_type",
        ),
    )

    # 26. Alerts
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("watch_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("monitoring_watches.id", ondelete="SET NULL"), nullable=True),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vendors.id"), nullable=True),
        sa.Column("severity", postgresql.ENUM(name="severity", create_type=False), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("status", postgresql.ENUM(name="alert_status", create_type=False), server_default=sa.text("'new'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # 27. Audit Log
    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("entity_type", sa.Text(), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("diff", postgresql.JSONB(), nullable=True),
        sa.Column("ip", postgresql.INET(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("audit_log_hospital_id_created_at_idx", "audit_log", ["hospital_id", sa.text("created_at DESC")])


def downgrade() -> None:
    # Drop tables in reverse foreign-key order
    tables = [
        "audit_log",
        "alerts",
        "monitoring_watches",
        "reviews",
        "reports",
        "integration_blueprints",
        "integration_checks",
        "dimension_scores",
        "timeline_events",
        "steering_commands",
        "debate_messages",
        "finding_evidence",
        "findings",
        "evidence",
        "agent_runs",
        "investigations",
        "document_chunks",
        "documents",
        "products",
        "vendors",
        "hospital_requirements",
        "requirement_catalogue",
        "hospital_systems",
        "users",
        "hospitals",
    ]
    for table in tables:
        op.drop_table(table)

    # Drop custom enums in reverse order
    for enum_name, _ in reversed(ENUMS):
        op.execute(f"DROP TYPE IF EXISTS {enum_name};")
