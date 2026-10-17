"""0001_initial_schema

Revision ID: 0001
Revises: 
Create Date: 2026-10-17

Creates:
  - Extensions: vector, pgcrypto
  - All 19 enum types
  - All 20 tables from bible section 4
  - Indexes (HNSW cosine on document_chunks.embedding, findings, evidence, audit_log)
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Extensions ──────────────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # ── Enum types ───────────────────────────────────────────────────────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE user_role AS ENUM ('admin','procurement','it','security','clinical','reviewer');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE system_category AS ENUM ('his_emr','lis','pacs','ris','erp','billing','abdm_gateway','other');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE deployment_model AS ENUM ('on_prem','private_cloud','public_cloud','hybrid','saas');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE risk_appetite AS ENUM ('conservative','balanced','aggressive');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE dimension AS ENUM ('compliance','security_privacy','clinical','financial','integration','operations');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE agent_name AS ENUM ('orchestrator','compliance','clinical_evidence','security_privacy','financial','integration_fit','operations','skeptic');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE finding_status AS ENUM ('supported','partially_supported','contradictory','unverified','insufficient_evidence','not_applicable');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE severity AS ENUM ('critical','high','medium','low','info');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE confidence AS ENUM ('high','medium','low');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE claim_origin AS ENUM ('vendor_claim','independently_verified','inferred');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE inv_status AS ENUM ('draft','queued','running','paused','completed','failed','cancelled');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE run_status AS ENUM ('pending','running','completed','failed','skipped');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE review_decision AS ENUM ('pending','accepted','rejected','edited');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE compat_status AS ENUM ('compatible','partial','incompatible','unknown');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE evidence_source AS ENUM ('vendor_document','government_portal','standard','research','public_web','hospital_data','catalogue');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE doc_status AS ENUM ('uploaded','processing','processed','failed');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE report_status AS ENUM ('draft','in_review','final');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE alert_status AS ENUM ('new','acknowledged','dismissed');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE debate_role AS ENUM ('claim','challenge','rebuttal','resolution');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ── Tables ───────────────────────────────────────────────────────────────

    # 4.2 Tenancy
    op.execute("""
        CREATE TABLE IF NOT EXISTS hospitals (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            name text NOT NULL,
            city text,
            state text,
            hospital_type text,
            bed_count int,
            nabh_accredited boolean DEFAULT false,
            abdm_maturity smallint CHECK (abdm_maturity BETWEEN 0 AND 5),
            risk_appetite risk_appetite DEFAULT 'balanced',
            annual_it_budget_inr bigint,
            data_residency text DEFAULT 'india_only',
            created_at timestamptz DEFAULT now(),
            updated_at timestamptz DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            hospital_id uuid NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
            email text UNIQUE NOT NULL,
            password_hash text NOT NULL,
            full_name text NOT NULL,
            role user_role NOT NULL DEFAULT 'procurement',
            is_active boolean DEFAULT true,
            created_at timestamptz DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS hospital_systems (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            hospital_id uuid NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
            category system_category NOT NULL,
            name text NOT NULL,
            vendor_name text,
            version text,
            standards jsonb DEFAULT '[]'::jsonb,
            interfaces jsonb DEFAULT '{}'::jsonb,
            deployment deployment_model,
            notes text,
            created_at timestamptz DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS requirement_catalogue (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            code text UNIQUE NOT NULL,
            dimension dimension NOT NULL,
            title text NOT NULL,
            description text,
            authority text,
            reference_url text,
            reference_date date,
            applies_to jsonb DEFAULT '{}'::jsonb,
            check_type text DEFAULT 'evidence',
            rule jsonb DEFAULT '{}'::jsonb,
            default_severity severity DEFAULT 'medium'
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS hospital_requirements (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            hospital_id uuid NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
            catalogue_id uuid REFERENCES requirement_catalogue(id),
            dimension dimension NOT NULL,
            title text NOT NULL,
            description text,
            mandatory boolean DEFAULT true,
            severity_if_unmet severity DEFAULT 'high',
            rule jsonb DEFAULT '{}'::jsonb,
            is_custom boolean DEFAULT false,
            created_at timestamptz DEFAULT now()
        )
    """)

    # 4.3 Vendors / documents
    op.execute("""
        CREATE TABLE IF NOT EXISTS vendors (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            hospital_id uuid NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
            name text NOT NULL,
            website text,
            country text DEFAULT 'India',
            cin text,
            contact_name text,
            contact_email text,
            notes text,
            created_at timestamptz DEFAULT now(),
            updated_at timestamptz DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            vendor_id uuid NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
            name text NOT NULL,
            category system_category NOT NULL,
            version text,
            description text,
            deployment_models jsonb DEFAULT '[]'::jsonb,
            claimed_standards jsonb DEFAULT '[]'::jsonb,
            claimed_certifications jsonb DEFAULT '[]'::jsonb,
            created_at timestamptz DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            hospital_id uuid NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
            vendor_id uuid NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
            product_id uuid REFERENCES products(id) ON DELETE SET NULL,
            doc_type text NOT NULL,
            filename text NOT NULL,
            storage_key text NOT NULL,
            mime_type text,
            size_bytes bigint,
            sha256 text,
            version_label text,
            doc_date date,
            valid_until date,
            status doc_status DEFAULT 'uploaded',
            error text,
            page_count int,
            uploaded_by uuid REFERENCES users(id),
            created_at timestamptz DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS document_chunks (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id uuid NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
            hospital_id uuid NOT NULL,
            chunk_index int NOT NULL,
            page int,
            content text NOT NULL,
            token_count int,
            embedding vector(1536)
        )
    """)

    # HNSW cosine index on embedding
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_hnsw
        ON document_chunks USING hnsw (embedding vector_cosine_ops)
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks (document_id)")

    # 4.4 Investigations
    op.execute("""
        CREATE TABLE IF NOT EXISTS investigations (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            hospital_id uuid NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
            vendor_id uuid NOT NULL REFERENCES vendors(id),
            product_id uuid REFERENCES products(id),
            created_by uuid REFERENCES users(id),
            title text NOT NULL,
            status inv_status DEFAULT 'draft',
            dimensions jsonb NOT NULL,
            instructions text,
            overall_score numeric(5,2),
            score_confidence numeric(4,3),
            overall_risk severity,
            summary text,
            started_at timestamptz,
            completed_at timestamptz,
            created_at timestamptz DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS agent_runs (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            investigation_id uuid NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
            agent agent_name NOT NULL,
            status run_status DEFAULT 'pending',
            progress smallint DEFAULT 0,
            current_task text,
            output jsonb,
            error text,
            token_usage jsonb,
            started_at timestamptz,
            finished_at timestamptz
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS evidence (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            hospital_id uuid NOT NULL,
            investigation_id uuid REFERENCES investigations(id) ON DELETE CASCADE,
            vendor_id uuid REFERENCES vendors(id),
            product_id uuid REFERENCES products(id),
            source_type evidence_source NOT NULL,
            source_name text NOT NULL,
            source_url text,
            document_id uuid REFERENCES documents(id),
            chunk_id uuid REFERENCES document_chunks(id),
            page int,
            excerpt text NOT NULL,
            doc_version text,
            source_date date,
            retrieved_at timestamptz DEFAULT now(),
            is_independent boolean DEFAULT false,
            reliability confidence DEFAULT 'medium',
            content_hash text
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS findings (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            investigation_id uuid NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
            hospital_id uuid NOT NULL,
            agent agent_name NOT NULL,
            dimension dimension NOT NULL,
            requirement_id uuid REFERENCES hospital_requirements(id),
            title text NOT NULL,
            description text NOT NULL,
            status finding_status NOT NULL,
            severity severity NOT NULL,
            evidence_confidence confidence NOT NULL,
            claim_origin claim_origin NOT NULL,
            recommended_action text,
            missing_evidence text,
            review_decision review_decision DEFAULT 'pending',
            created_at timestamptz DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS finding_evidence (
            finding_id uuid REFERENCES findings(id) ON DELETE CASCADE,
            evidence_id uuid REFERENCES evidence(id) ON DELETE CASCADE,
            relation text CHECK (relation IN ('supports','contradicts','context')),
            PRIMARY KEY (finding_id, evidence_id)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS debate_messages (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            investigation_id uuid NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
            finding_id uuid REFERENCES findings(id) ON DELETE SET NULL,
            seq int NOT NULL,
            agent agent_name NOT NULL,
            role debate_role NOT NULL,
            content text NOT NULL,
            evidence_ids jsonb DEFAULT '[]'::jsonb,
            created_at timestamptz DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS steering_commands (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            investigation_id uuid NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
            user_id uuid REFERENCES users(id),
            instruction text NOT NULL,
            parsed jsonb,
            status text DEFAULT 'received',
            created_at timestamptz DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS timeline_events (
            id bigserial PRIMARY KEY,
            investigation_id uuid NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
            event text NOT NULL,
            agent agent_name,
            payload jsonb,
            created_at timestamptz DEFAULT now()
        )
    """)

    # 4.5 Scoring / reports / monitoring / audit
    op.execute("""
        CREATE TABLE IF NOT EXISTS dimension_scores (
            investigation_id uuid REFERENCES investigations(id) ON DELETE CASCADE,
            dimension dimension,
            score numeric(5,2) NOT NULL,
            weight numeric(4,3) NOT NULL,
            confidence numeric(4,3) NOT NULL,
            rationale text,
            computed_at timestamptz DEFAULT now(),
            PRIMARY KEY (investigation_id, dimension)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS integration_checks (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            investigation_id uuid NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
            hospital_system_id uuid REFERENCES hospital_systems(id),
            requirement text NOT NULL,
            vendor_capability text,
            status compat_status NOT NULL,
            gap_description text,
            effort text CHECK (effort IN ('low','medium','high')),
            recommendation text,
            evidence_ids jsonb DEFAULT '[]'::jsonb,
            evidence_confidence confidence DEFAULT 'medium'
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS integration_blueprints (
            investigation_id uuid PRIMARY KEY REFERENCES investigations(id) ON DELETE CASCADE,
            readiness_score numeric(5,2),
            phases jsonb NOT NULL,
            risks jsonb,
            generated_at timestamptz DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            investigation_id uuid NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
            hospital_id uuid NOT NULL,
            version int DEFAULT 1,
            status report_status DEFAULT 'draft',
            summary jsonb NOT NULL,
            storage_key text,
            generated_by uuid REFERENCES users(id),
            signed_off_by uuid REFERENCES users(id),
            signed_off_at timestamptz,
            created_at timestamptz DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            finding_id uuid NOT NULL REFERENCES findings(id) ON DELETE CASCADE,
            reviewer_id uuid NOT NULL REFERENCES users(id),
            decision review_decision NOT NULL,
            comment text,
            edited_severity severity,
            edited_status finding_status,
            created_at timestamptz DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS monitoring_watches (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            hospital_id uuid NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
            vendor_id uuid REFERENCES vendors(id),
            product_id uuid REFERENCES products(id),
            watch_type text CHECK (watch_type IN ('certificate_expiry','cve','regulatory','document_change')),
            config jsonb DEFAULT '{}'::jsonb,
            active boolean DEFAULT true,
            last_run_at timestamptz
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            hospital_id uuid NOT NULL,
            watch_id uuid REFERENCES monitoring_watches(id) ON DELETE SET NULL,
            vendor_id uuid REFERENCES vendors(id),
            severity severity NOT NULL,
            title text NOT NULL,
            detail text,
            source_url text,
            status alert_status DEFAULT 'new',
            created_at timestamptz DEFAULT now()
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id bigserial PRIMARY KEY,
            hospital_id uuid,
            user_id uuid,
            action text NOT NULL,
            entity_type text NOT NULL,
            entity_id uuid,
            diff jsonb,
            ip inet,
            created_at timestamptz DEFAULT now()
        )
    """)

    # ── Additional indexes ───────────────────────────────────────────────────
    op.execute("CREATE INDEX IF NOT EXISTS idx_findings_inv_dim ON findings (investigation_id, dimension)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_evidence_investigation_id ON evidence (investigation_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_hospital_created ON audit_log (hospital_id, created_at DESC)")


def downgrade() -> None:
    # Drop in reverse dependency order
    op.execute("DROP TABLE IF EXISTS audit_log CASCADE")
    op.execute("DROP TABLE IF EXISTS alerts CASCADE")
    op.execute("DROP TABLE IF EXISTS monitoring_watches CASCADE")
    op.execute("DROP TABLE IF EXISTS reviews CASCADE")
    op.execute("DROP TABLE IF EXISTS reports CASCADE")
    op.execute("DROP TABLE IF EXISTS integration_blueprints CASCADE")
    op.execute("DROP TABLE IF EXISTS integration_checks CASCADE")
    op.execute("DROP TABLE IF EXISTS dimension_scores CASCADE")
    op.execute("DROP TABLE IF EXISTS timeline_events CASCADE")
    op.execute("DROP TABLE IF EXISTS steering_commands CASCADE")
    op.execute("DROP TABLE IF EXISTS debate_messages CASCADE")
    op.execute("DROP TABLE IF EXISTS finding_evidence CASCADE")
    op.execute("DROP TABLE IF EXISTS findings CASCADE")
    op.execute("DROP TABLE IF EXISTS evidence CASCADE")
    op.execute("DROP TABLE IF EXISTS agent_runs CASCADE")
    op.execute("DROP TABLE IF EXISTS investigations CASCADE")
    op.execute("DROP TABLE IF EXISTS document_chunks CASCADE")
    op.execute("DROP TABLE IF EXISTS documents CASCADE")
    op.execute("DROP TABLE IF EXISTS products CASCADE")
    op.execute("DROP TABLE IF EXISTS vendors CASCADE")
    op.execute("DROP TABLE IF EXISTS hospital_requirements CASCADE")
    op.execute("DROP TABLE IF EXISTS requirement_catalogue CASCADE")
    op.execute("DROP TABLE IF EXISTS hospital_systems CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    op.execute("DROP TABLE IF EXISTS hospitals CASCADE")

    # Drop enums
    for enum_name in [
        "debate_role", "alert_status", "report_status", "doc_status",
        "evidence_source", "compat_status", "review_decision", "run_status",
        "inv_status", "claim_origin", "confidence", "severity",
        "finding_status", "agent_name", "dimension", "risk_appetite",
        "deployment_model", "system_category", "user_role",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name} CASCADE")
