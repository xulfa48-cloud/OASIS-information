from fastapi import FastAPI
from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import re
import httpx
import logging
import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

# Basic logging
logger = logging.getLogger('novelty-engine')
logging.basicConfig(level=os.getenv('LOG_LEVEL', 'INFO'))

app = FastAPI(title="Novelty Engine", version="1.0.0")

# Environment / configuration
KG_SERVICE_URL = os.getenv('KG_SERVICE_URL', 'http://knowledge-graph-service:8081')
EMBEDDING_PROVIDER_URL = os.getenv('EMBEDDING_PROVIDER_URL')
EMBEDDING_PROVIDER_KEY = os.getenv('EMBEDDING_PROVIDER_KEY')
API_KEY = os.getenv('SERVICE_API_KEY')  # shared service-to-service API key
REQUEST_TIMEOUT = float(os.getenv('NOVELTY_TIMEOUT', '15.0'))
MAX_RETRIES = int(os.getenv('NOVELTY_MAX_RETRIES', '3'))

# Observability
REQUESTS = Counter('oasis_novelty_requests_total', 'Total novelty requests', ['status'])
DURATION = Histogram('oasis_novelty_request_duration_seconds', 'Novelty request duration seconds')

# Simple redaction patterns
EMAIL_RE = re.compile(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d\s\-()]{7,}\d")

class NoveltyRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=20000, description="Text to score for novelty")
    top_k: Optional[int] = Field(10, ge=1, le=100, description="Number of nearest neighbors to consider")
    context_ids: Optional[List[str]] = None

class NoveltyResponse(BaseModel):
    score: float
    details: Dict[str, Any]


def redact(text: str) -> str:
    t = EMAIL_RE.sub('[REDACTED_EMAIL]', text)
    t = PHONE_RE.sub('[REDACTED_PHONE]', t)
    return t

async def fetch_embedding(text: str) -> List[float]:
    """Call external embedding provider. Expects JSON {"input": "..."} -> {"embedding": [...]}"""
    if not EMBEDDING_PROVIDER_URL or not EMBEDDING_PROVIDER_KEY:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='embedding provider not configured')

    headers = {"Authorization": f"Bearer {EMBEDDING_PROVIDER_KEY}", "Content-Type": "application/json"}
    payload = {"input": text}
    backoff = 0.5
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                r = await client.post(EMBEDDING_PROVIDER_URL, json=payload, headers=headers)
                if r.status_code == 200:
                    data = r.json()
                    emb = data.get('embedding')
                    if not isinstance(emb, list):
                        raise HTTPException(status_code=502, detail='invalid embedding response')
                    return emb
                if r.status_code in (429, 502, 503, 504):
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                raise HTTPException(status_code=502, detail='embedding provider error')
        except httpx.RequestError as e:
            logger.warning('embedding_request_error', error=str(e), attempt=attempt)
            await asyncio.sleep(backoff)
            backoff *= 2
    raise HTTPException(status_code=502, detail='embedding provider unavailable')


async def kg_vector_search(embedding: List[float], k: int) -> List[Dict[str, Any]]:
    """Query KG service for nearest neighbors using vector search API.
    Expects KG to expose POST /api/v1/kg/search with {"query_embedding": [...], "k": int}
    Returns list of nodes with distance.
    """
    url = f"{KG_SERVICE_URL}/api/v1/kg/search"
    payload = {"query_embedding": embedding, "k": k}
    headers = {"Content-Type": "application/json"}
    backoff = 0.5
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                r = await client.post(url, json=payload, headers=headers)
                if r.status_code == 200:
                    return r.json().get('results', [])
                if r.status_code in (429, 502, 503, 504):
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                logger.error('kg_search_error', status=r.status_code, body=r.text)
                raise HTTPException(status_code=502, detail='kg search failed')
        except httpx.RequestError as e:
            logger.warning('kg_search_request_error', error=str(e), attempt=attempt)
            await asyncio.sleep(backoff)
            backoff *= 2
    raise HTTPException(status_code=502, detail='kg service unavailable')


def compute_novelty_score(distances: List[float], max_distance: float = 2.0) -> float:
    """Compute a novelty score in [0,1] where 1 is highly novel.
    Use distance-based scoring: if nearest neighbors are far, novelty increases.
    """
    if not distances:
        return 1.0
    # Normalize distances to [0,1] using a soft threshold
    norm = [min(d / max_distance, 1.0) for d in distances]
    # Higher normalized distance -> more novel -> compute mean
    score = sum(norm) / len(norm)
    # Bound and invert so that large distance -> score closer to 1
    return round(score, 4)


@app.get('/api/v1/health')
async def health():
    return {"status": "ok"}

@app.get('/api/v1/ready')
async def ready():
    # readiness: embedding provider presence
    if not EMBEDDING_PROVIDER_URL or not EMBEDDING_PROVIDER_KEY:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='embedding provider not configured')
    return {"status": "ready"}

@app.get('/metrics')
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post('/api/v1/novelty/score', response_model=NoveltyResponse)
async def score(req: NoveltyRequest, x_api_key: Optional[str] = None):
    start = time.time()
    try:
        # Lightweight service-to-service API key
        if API_KEY and x_api_key != API_KEY:
            raise HTTPException(status_code=401, detail='invalid api key')

        text = redact(req.text)
        # Get embedding for the input text
        emb = await fetch_embedding(text)
        # Query KG for nearest neighbors
        neighbors = await kg_vector_search(emb, req.top_k)
        distances = [n.get('distance', 0.0) for n in neighbors]
        score_value = compute_novelty_score(distances)
        details = {
            'neighbor_count': len(neighbors),
            'sample_neighbors': [
                {'id': n.get('id'), 'distance': n.get('distance')} for n in neighbors[:5]
            ]
        }
        REQUESTS.labels(status='ok').inc()
        DURATION.observe(time.time() - start)
        return NoveltyResponse(score=score_value, details=details)
    except HTTPException:
        REQUESTS.labels(status='error').inc()
        raise
    except Exception as e:
        logger.exception('novelty_error')
        REQUESTS.labels(status='error').inc()
        raise HTTPException(status_code=500, detail='internal server error')
