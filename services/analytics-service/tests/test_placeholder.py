import asyncio
import uuid
import os
import pytest

try:
    import asyncpg
except Exception:
    asyncpg = None

POSTGRES_DSN = os.getenv('POSTGRES_DSN', '')

@pytest.mark.asyncio
async def test_analytics_metrics_recording_and_retention():
    if not POSTGRES_DSN or asyncpg is None:
        pytest.skip('POSTGRES_DSN not set or asyncpg not installed')

    schema = f'test_analytics_{uuid.uuid4().hex[:8]}'
    table = 'metrics'

    conn = await asyncpg.connect(dsn=POSTGRES_DSN)
    try:
        await conn.execute(f'CREATE SCHEMA IF NOT EXISTS {schema}')
        await conn.execute(f"CREATE TABLE {schema}.{table} (id UUID PRIMARY KEY, name TEXT NOT NULL, value DOUBLE PRECISION NOT NULL, created_at TIMESTAMPTZ DEFAULT now())")

        mid = uuid.uuid4()
        await conn.execute(f"INSERT INTO {schema}.{table} (id, name, value) VALUES ($1, $2, $3)", mid, 'request_latency', 123.4)

        row = await conn.fetchrow(f"SELECT value FROM {schema}.{table} WHERE id = $1", mid)
        assert row['value'] == 123.4

        # Retention: simulate deletion of old metrics
        await conn.execute(f"DELETE FROM {schema}.{table} WHERE created_at < now() - interval '1 day'")

    finally:
        await conn.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
        await conn.close()
