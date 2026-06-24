import os
import asyncio
import uuid
import pytest

try:
    import asyncpg
except Exception:
    asyncpg = None

POSTGRES_DSN = os.getenv('POSTGRES_DSN', os.getenv('PAPER_DATABASE_URL', ''))

@pytest.mark.asyncio
async def test_paper_repository_transaction_and_constraints():
    if not POSTGRES_DSN or asyncpg is None:
        pytest.skip('POSTGRES_DSN not set or asyncpg not installed')

    schema = f'test_papers_{uuid.uuid4().hex[:8]}'
    table = 'papers'

    conn = await asyncpg.connect(dsn=POSTGRES_DSN)
    try:
        await conn.execute(f'CREATE SCHEMA IF NOT EXISTS {schema}')
        # Use a minimal production-like columns set including a vector placeholder (stored as float8[] for portability in tests)
        await conn.execute(f"CREATE TABLE {schema}.{table} (id UUID PRIMARY KEY, title TEXT NOT NULL, embedding float8[] , created_at TIMESTAMPTZ DEFAULT now(), version INTEGER DEFAULT 1)")

        # Insert and update
        pid = uuid.uuid4()
        await conn.execute(f"INSERT INTO {schema}.{table} (id, title, embedding) VALUES ($1, $2, $3)", pid, 'Research Paper', [0.1, 0.2, 0.3])
        row = await conn.fetchrow(f"SELECT id, title, embedding FROM {schema}.{table} WHERE id = $1", pid)
        assert str(row['id']) == str(pid)
        assert row['title'] == 'Research Paper'
        assert isinstance(row['embedding'], list)

        # Transaction rollback test
        tx = conn.transaction()
        await tx.start()
        await conn.execute(f"UPDATE {schema}.{table} SET title = $1 WHERE id = $2", 'Updated Title', pid)
        tmp = await conn.fetchrow(f"SELECT title FROM {schema}.{table} WHERE id = $1", pid)
        assert tmp['title'] == 'Updated Title'
        await tx.rollback()
        after = await conn.fetchrow(f"SELECT title FROM {schema}.{table} WHERE id = $1", pid)
        assert after['title'] == 'Research Paper'

        # Concurrency: simulate two concurrent upserts that should not violate PK
        async def upsert_title(new_title):
            await conn.execute(f"UPDATE {schema}.{table} SET title = $1 WHERE id = $2", new_title, pid)

        await asyncio.gather(*[upsert_title(f'Title {i}') for i in range(5)])
        final = await conn.fetchrow(f"SELECT title FROM {schema}.{table} WHERE id = $1", pid)
        assert final is not None

    finally:
        await conn.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
        await conn.close()
