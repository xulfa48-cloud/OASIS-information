import os
import asyncio
import uuid
import pytest

try:
    import asyncpg
except Exception:
    asyncpg = None

POSTGRES_DSN = os.getenv('POSTGRES_DSN', os.getenv('NOVELTY_DATABASE_URL', ''))

@pytest.mark.asyncio
async def test_repository_crud_and_transaction_behavior():
    if not POSTGRES_DSN or asyncpg is None:
        pytest.skip('POSTGRES_DSN not set or asyncpg not installed')

    # Create a temporary schema and table to test repository behaviors without relying on migrations
    schema = f'test_schema_{uuid.uuid4().hex[:8]}'
    table = 'sources'

    conn = await asyncpg.connect(dsn=POSTGRES_DSN)
    try:
        await conn.execute(f'CREATE SCHEMA IF NOT EXISTS {schema}')
        await conn.execute(f"CREATE TABLE {schema}.{table} (id UUID PRIMARY KEY, name TEXT NOT NULL UNIQUE, created_at TIMESTAMPTZ DEFAULT now(), version INTEGER DEFAULT 1)")

        # Insert
        uid = uuid.uuid4()
        await conn.execute(f"INSERT INTO {schema}.{table} (id, name) VALUES ($1, $2)", uid, 'source-a')

        row = await conn.fetchrow(f"SELECT id, name, version FROM {schema}.{table} WHERE id = $1", uid)
        assert str(row['id']) == str(uid)
        assert row['name'] == 'source-a'
        assert row['version'] == 1

        # Update within transaction and rollback
        tx = conn.transaction()
        await tx.start()
        await conn.execute(f"UPDATE {schema}.{table} SET name = $1, version = version + 1 WHERE id = $2", 'source-a-updated', uid)
        row_tx = await conn.fetchrow(f"SELECT name, version FROM {schema}.{table} WHERE id = $1", uid)
        assert row_tx['name'] == 'source-a-updated'
        assert row_tx['version'] == 2
        await tx.rollback()

        row_after = await conn.fetchrow(f"SELECT name, version FROM {schema}.{table} WHERE id = $1", uid)
        assert row_after['name'] == 'source-a'
        assert row_after['version'] == 1

        # Constraint violation (unique)
        with pytest.raises(asyncpg.exceptions.UniqueViolationError):
            await conn.execute(f"INSERT INTO {schema}.{table} (id, name) VALUES ($1, $2)", uuid.uuid4(), 'source-a')

        # Delete
        await conn.execute(f"DELETE FROM {schema}.{table} WHERE id = $1", uid)
        row_deleted = await conn.fetchrow(f"SELECT id FROM {schema}.{table} WHERE id = $1", uid)
        assert row_deleted is None

    finally:
        # cleanup
        await conn.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
        await conn.close()
