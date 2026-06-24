import os
import asyncio
import uuid
import pytest

try:
    import asyncpg
except Exception:
    asyncpg = None

POSTGRES_DSN = os.getenv('EXPORT_DATABASE_URL', os.getenv('POSTGRES_DSN', ''))

@pytest.mark.asyncio
async def test_export_job_lifecycle_and_constraints():
    if not POSTGRES_DSN or asyncpg is None:
        pytest.skip('POSTGRES_DSN not set or asyncpg not installed')

    schema = f'test_export_{uuid.uuid4().hex[:8]}'
    table = 'export_jobs'

    conn = await asyncpg.connect(dsn=POSTGRES_DSN)
    try:
        await conn.execute(f'CREATE SCHEMA IF NOT EXISTS {schema}')
        await conn.execute(f"CREATE TABLE {schema}.{table} (id UUID PRIMARY KEY, user_id UUID NOT NULL, status TEXT NOT NULL, artifact_url TEXT, created_at TIMESTAMPTZ DEFAULT now())")

        # Insert job
        jid = uuid.uuid4()
        uid = uuid.uuid4()
        await conn.execute(f"INSERT INTO {schema}.{table} (id, user_id, status) VALUES ($1, $2, $3)", jid, uid, 'pending')

        # Transition lifecycle
        await conn.execute(f"UPDATE {schema}.{table} SET status = $1 WHERE id = $2", 'completed', jid)
        row = await conn.fetchrow(f"SELECT status FROM {schema}.{table} WHERE id = $1", jid)
        assert row['status'] == 'completed'

        # Constraint: user_id not null
        with pytest.raises(asyncpg.exceptions.NotNullViolationError):
            await conn.execute(f"INSERT INTO {schema}.{table} (id, status) VALUES ($1, $2)", uuid.uuid4(), 'pending')

        # Delete and ensure removal
        await conn.execute(f"DELETE FROM {schema}.{table} WHERE id = $1", jid)
        row2 = await conn.fetchrow(f"SELECT id FROM {schema}.{table} WHERE id = $1", jid)
        assert row2 is None

    finally:
        await conn.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
        await conn.close()
