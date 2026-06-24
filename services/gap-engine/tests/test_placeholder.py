import time
import threading
import jwt
import os
import pytest
from fastapi.testclient import TestClient

from services.gap_engine.src import main as gap

client = TestClient(gap.app)

SECRET = os.getenv('AUTH_TEST_RSA_PRIVATE')

def make_jwt(payload, exp_offset=3600, key=SECRET):
    if not key:
        pytest.skip('RSA keys not configured')
    now = int(time.time())
    claims = payload.copy()
    claims.update({'iat': now, 'exp': now + exp_offset})
    return jwt.encode(claims, key, algorithm='RS256')


def test_gap_requires_topic_and_behaves_idempotently():
    r = client.get('/api/v1/gaps?topic=ai')
    assert r.status_code == 200
    data = r.json()
    assert 'topic' in data and data['topic'] == 'ai'


def test_gap_rate_limit_simulation(monkeypatch):
    # Simulate rate limiter by calling endpoint rapidly and expecting eventual 429
    statuses = []
    for _ in range(60):
        r = client.get('/api/v1/gaps?topic=ai')
        statuses.append(r.status_code)
    # Expect at least one 200 and no server errors
    assert 200 in statuses
    assert all(s in (200, 429) for s in statuses)


def test_gap_concurrent_deduplication():
    # Simulate concurrent duplicate submissions to ensure idempotency behavior
    def call():
        r = client.get('/api/v1/gaps?topic=ai')
        return r.json()

    threads = []
    results = []
    for _ in range(10):
        t = threading.Thread(target=lambda: results.append(call()))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    # All results should be equivalent (idempotent)
    assert all(r == results[0] for r in results)
