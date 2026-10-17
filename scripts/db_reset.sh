#!/usr/bin/env bash
# scripts/db_reset.sh
# Drop all KYRO tables and re-run migrations from scratch.
# Usage: bash scripts/db_reset.sh
# WARNING: Destroys all data. For local development only.

set -euo pipefail

cd "$(dirname "$0")/.."

echo "⚠️  Dropping all tables and re-running migrations..."
backend/venv/bin/alembic -c backend/alembic.ini downgrade base
backend/venv/bin/alembic -c backend/alembic.ini upgrade head
echo "✅  Database reset complete."
