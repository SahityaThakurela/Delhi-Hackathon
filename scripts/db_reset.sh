#!/usr/bin/env bash
set -e

# KYRO Database Reset Script
# Drops schema objects and runs alembic upgrade head

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

cd "$PROJECT_ROOT/backend"

echo "Resetting database..."
python -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def reset():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        print('Dropping schema public cascade...')
        await conn.execute(text('DROP SCHEMA public CASCADE; CREATE SCHEMA public;'))
        await conn.execute(text('GRANT ALL ON SCHEMA public TO postgres; GRANT ALL ON SCHEMA public TO public;'))
    await engine.dispose()
    print('Public schema reset completed.')

asyncio.run(reset())
"

echo "Running migrations: alembic upgrade head..."
alembic upgrade head

echo "Database reset and migration to head completed successfully!"
