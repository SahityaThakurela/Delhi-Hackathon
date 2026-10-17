# KYRO — Autonomous Healthcare Vendor Intelligence Platform

> **Hack-4-Crown | Team LUNA**  
> AI-Powered Vendor Risk Assessment & Integration Compatibility Engine for Indian Hospitals.  
> *Evidence-driven vendor investigation, not automated vendor certification.*

---

## 1. Architecture & Team Ownership Split

Per the **KYRO Team Build Bible**:

| Member | Role | Ownership & Deliverables |
|---|---|---|
| **P1** | **Core Backend & Database** | Postgres schema & migrations, seed data, auth (JWT), hospital profile, vendors/products, document upload & storage, reviews, reports (PDF), monitoring CRUD, audit log, dashboard, OpenAPI export. |
| **P2** *(This Branch)* | **AI, Agents & Real-Time Intelligence** | Document parsing & chunking, embeddings & RAG, deterministic checks, LangGraph orchestrator & 7 specialist agents, investigations/findings/evidence/trust/integration endpoints, Socket.IO realtime, trust score engine, integration compatibility engine, monitoring intelligence jobs. |
| **P3** | **Frontend Application** | Next.js App Router, Stitch-to-code design system, API client, live investigation UI, Live Debate view, Evidence Explorer, charts, mock mode (MSW). |

---

## 2. P2 Backend Structure

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app + Socket.IO mount (/ws) + Health checks
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/                     # REST API (/api/v1)
│   │       ├── __init__.py
│   │       ├── investigations.py   # Investigation lifecycle, steer, debate, timeline
│   │       ├── findings.py         # Findings queries and filters
│   │       ├── evidence.py         # Evidence explorer and ad-hoc claim verification
│   │       ├── trust.py            # Deterministic trust score computation
│   │       └── integration.py      # Integration compatibility matrix & blueprints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── deterministic.py        # Rule-based validation (no LLM): cert validity, VAPT recency, version matching, ABDM checks
│   │   ├── scoring.py              # Section 11.1 deterministic scoring formula & risk calculation
│   │   ├── integration_engine.py   # Compatibility engine & multi-phase blueprint generator
│   │   ├── ingestion.py            # Document parsing, chunking, prompt-injection hygiene
│   │   └── rag.py                  # Scoped vector search & citable chunk retrieval
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py                 # Abstract base class for specialist agents
│   │   ├── orchestrator.py         # LangGraph orchestrator coordinator
│   │   ├── prompts/                # Agent system prompts
│   │   └── tools/                  # External APIs (NVD CVE, PubMed, ClinicalTrials.gov)
│   ├── realtime/
│   │   ├── __init__.py
│   │   ├── server.py               # python-socketio AsyncServer mounted at /ws
│   │   └── emit.py                 # Monotonic sequence event emitter with contract envelope
│   ├── models/
│   │   ├── __init__.py
│   │   └── ai_models.py            # P2 AI-specific model extensions (models/ai_*.py only)
│   └── schemas/
│       ├── __init__.py
│       └── ai_schemas.py           # Strict Pydantic models & enums per Bible Sections 4 & 5
├── tests/
│   ├── __init__.py
│   └── test_p2_smoke.py            # P2 smoke test suite covering imports, routes, logic
├── requirements.txt                # Python dependencies
└── .env.example                    # Environment template
```

---

## 3. P2 Backend Setup Instructions

### Prerequisites
- Python 3.10+ (Python 3.11 recommended per Bible)
- Virtual environment (`venv` or `uv`)

### Step 1: Clone and Navigate to Branch
```bash
git checkout p2/ai-agents-realtime
```

### Step 2: Set Up Virtual Environment
```bash
python -m venv .venv
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### Step 4: Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure you provide your `OPENAI_API_KEY` for AI agent tasks once ready.

### Step 5: Run Smoke Tests
```bash
python -m pytest backend/tests -v
```

### Step 6: Launch Development Server
```bash
uvicorn backend.app.main:app --reload --port 8000
```
- Interactive Swagger API Documentation: `http://localhost:8000/docs`
- Health Check Liveness Probe: `http://localhost:8000/api/v1/health`
- Real-Time Socket.IO Endpoint: `http://localhost:8000/ws` (namespace `/investigations`)

---

## 4. Components That P1 Must Provide (Handoff Contract)

Per the **KYRO Team Build Bible**, P2 strictly avoids duplicate implementations and expects P1 to supply the following shared backend foundation components:

1. **Database Session & Base (`backend/app/db/`)**:
   - `session.py`: Async engine, sessionmaker, `get_db` FastAPI dependency with Supabase pool settings (`pool_pre_ping=True`).
   - `base.py`: SQLAlchemy `DeclarativeBase` with UUID primary keys and timestamp mixins (`created_at`, `updated_at`).
   - `tenancy.py`: `scoped(query, model, hospital_id)` query helper enforcing multi-tenant isolation.
2. **Core Database Models (`backend/app/models/`)**:
   - `hospital.py`: `hospitals`, `users`, `hospital_systems`
   - `requirements.py`: `requirement_catalogue`, `hospital_requirements`
   - `vendor.py`: `vendors`, `products`
   - `document.py`: `documents`, `document_chunks` (with pgvector `Vector(1536)` HNSW index)
   - `investigation.py`: `investigations`, `agent_runs`, `timeline_events`, `steering_commands`
   - `evidence.py`: `evidence`, `findings`, `finding_evidence`, `debate_messages`
   - `scoring.py`: `dimension_scores`, `integration_checks`, `integration_blueprints`
   - `reports.py`: `reports`, `reviews`
   - `monitoring.py`: `monitoring_watches`, `alerts`
   - `audit.py`: `audit_log`
3. **Database Migrations (`alembic/`)**:
   - Migration 0001 enabling extensions `vector` and `pgcrypto`, creating enums, tables, FKs, and HNSW cosine index on `document_chunks.embedding`.
4. **Configuration & Security (`backend/app/core/`)**:
   - `config.py`: `pydantic-settings` Settings class reading every `.env` variable.
   - `security.py`: Password hashing (Argon2 / bcrypt) and JWT generation/verification (`sub`, `hospital_id`, `role`).
   - `deps.py`: FastAPI security dependencies (`get_current_user`, `get_hospital_id`, `require_roles`, `require_reviewer`).
   - `errors.py`: Standard `AppError` and validation error mappers returning `{"error": {"code", "message", "details"}}`.
5. **Shared Storage & Audit Services (`backend/app/services/`)**:
   - `storage.py`: S3-compatible client (`put`, `signed_url`, `delete`) with local disk fallback.
   - `audit.py`: `log(db, user, action, entity_type, entity_id, diff)` audit logging utility.
6. **Core REST Routes (`backend/app/api/v1/`)**:
   - Auth (`/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/me`)
   - Hospital Profile & Systems (`/hospital`, `/hospital/completeness`, `/hospital/systems`)
   - Requirements Catalogue (`/requirements/catalogue`, `/hospital/requirements`)
   - Vendors & Products (`/vendors`, `/vendors/{id}`, `/vendors/compare`, `/products/{id}`)
   - Document Intake (`/documents/upload`, `/documents/{id}/download`, `DELETE /documents/{id}`)
   - Reports & Reviews (`/reports`, `/findings/{id}/review`)
   - Monitoring CRUD (`/monitoring/watches`, `/monitoring/alerts`)
   - Dashboard Summary (`/dashboard/summary`) & Audit Log (`/audit-log`)
