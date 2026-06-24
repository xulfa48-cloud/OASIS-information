import os
import time
import logging
import structlog
import httpx
import asyncio
from typing import List, Optional, Dict, Any
from functools import wraps

from fastapi import FastAPI, Depends, HTTPException, status, Header, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import jwt

# Structured logging
structlog.configure(processors=[structlog.processors.TimeStamper(fmt="iso"), structlog.processors.JSONRenderer()])
logger = structlog.get_logger('ai-copilot')

app = FastAPI(title="OASIS AI Copilot Service", version="1.0.0")

# Environment configuration
COPILOT_PROVIDER_URL = os.getenv('COPILOT_PROVIDER_URL')
COPILOT_PROVIDER_KEY = os.getenv('COPILOT_PROVIDER_API_KEY')
KG_SERVICE_URL = os.getenv('KG_SERVICE_URL', 'http://knowledge-graph-service:8081')
COPILOT_REQUEST_TIMEOUT = float(os.getenv('COPILOT_REQUEST_TIMEOUT', '30.0'))
COPILOT_MAX_RETRIES = int(os.getenv('COPILOT_MAX_RETRIES', '3'))
JWT_PUBLIC_KEY = os.getenv('AUTH_JWT_PUBLIC')  # RSA public key in PEM format
JWT_ALGORITHM = os.getenv('AUTH_JWT_ALGORITHM', 'RS256')
RATE_LIMIT_REDIS = os.getenv('RATE_LIMIT_REDIS_URL')
RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', '60'))

# Observability
REQUESTS = Counter('oasis_copilot_requests_total', 'Total copilot requests', ['endpoint', 'status'])
DURATION = Histogram('oasis_copilot_request_duration_seconds', 'Request duration seconds', ['endpoint'])

security = HTTPBearer()

# Simple RBAC roles map for endpoints
ENDPOINT_ROLES = {
    '/api/v1/copilot/query': ['copilot', 'researcher', 'admin']
}

class CopilotRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=8000)
    context_ids: Optional[List[str]] = None
    max_tokens: Optional[int] = Field(512, ge=16, le=2048)

class CopilotResponse(BaseModel):
    response: str
    model: str
    latency_ms: int

# Utility: Validate and decode JWT
def decode_jwt(token: str) -> Dict[str, Any]:
    if not JWT_PUBLIC_KEY:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='Auth public key not configured')
    try:
        payload = jwt.decode(token, JWT_PUBLIC_KEY, algorithms=[JWT_ALGORITHM], options={"require": ["exp", "iat", "sub"]})
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='token expired')
    except jwt.InvalidSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='invalid token signature')
    except jwt.DecodeError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='invalid token')

# Dependency: authenticate and authorize
async def auth_dependency(credentials: HTTPAuthorizationCredentials = Depends(security), request: Request = None):
    token = credentials.credentials
    payload = decode_jwt(token)
    # attach identity to request.state for downstream use
    request.state.user = payload
    # RBAC enforcement
    path = request.url.path
    allowed = ENDPOINT_ROLES.get(path, [])
    user_roles = payload.get('roles', [])
    if allowed and not any(r in user_roles for r in allowed):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='forbidden')
    return payload

# Rate limiter - lightweight, in-memory fallback
_rate_limits: Dict[str, Dict[str, Any]] = {}

async def rate_limiter(key: str):
    now = int(time.time())
    window = now // 60
    entry = _rate_limits.get(key)
    if entry and entry.get('window') == window:
        if entry['count'] >= RATE_LIMIT_PER_MINUTE:
            return False
        entry['count'] += 1
    else:
        _rate_limits[key] = {'window': window, 'count': 1}
    return True

# Helper: call external LLM provider with retries and backoff
async def call_provider(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not COPILOT_PROVIDER_URL or not COPILOT_PROVIDER_KEY:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='LLM provider not configured')

    headers = {"Authorization": f"Bearer {COPILOT_PROVIDER_KEY}", "Content-Type": "application/json"}
    backoff = 0.5
    for attempt in range(1, COPILOT_MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=COPILOT_REQUEST_TIMEOUT) as client:
                r = await client.post(COPILOT_PROVIDER_URL, json=payload, headers=headers)
                if r.status_code == 200:
                    return r.json()
                # 429 or 5xx: retry
                if r.status_code in (429, 502, 503, 504):
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                # Non-retryable
                raise HTTPException(status_code=502, detail='llm provider error')
        except httpx.RequestError as e:
            logger.warn('provider_request_error', error=str(e), attempt=attempt)
            await asyncio.sleep(backoff)
            backoff *= 2
    raise HTTPException(status_code=502, detail='llm provider unavailable')

# Redaction helper
import re
EMAIL_RE = re.compile(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d\s\-()]{7,}\d")

def redact(text: str) -> str:
    t = EMAIL_RE.sub('[REDACTED_EMAIL]', text)
    t = PHONE_RE.sub('[REDACTED_PHONE]', t)
    return t

@app.get('/api/v1/health')
async def health():
    return {"status": "ok"}

@app.get('/api/v1/ready')
async def ready():
    # readiness checks: provider key and JWT public key at minimum
    if not JWT_PUBLIC_KEY:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='auth not configured')
    if not COPILOT_PROVIDER_KEY:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail='llm provider not configured')
    return {"status": "ready"}

@app.get('/metrics')
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post('/api/v1/copilot/query', response_model=CopilotResponse)
async def query(req: CopilotRequest, creds: Dict = Depends(auth_dependency)):
    start = time.time()
    endpoint = '/api/v1/copilot/query'
    # rate limiting by subject
    subject = creds.get('sub')
    allowed = await rate_limiter(subject or 'anon')
    if not allowed:
        REQUESTS.labels(endpoint=endpoint, status='rate_limited').inc()
        raise HTTPException(status_code=429, detail='rate limit exceeded')

    # build context by calling KG service if needed
    context_text = ''
    if req.context_ids:
        parts: List[str] = []
        async with httpx.AsyncClient(timeout=5.0) as client:
            for cid in req.context_ids:
                try:
                    r = await client.get(f"{KG_SERVICE_URL}/api/v1/kg/nodes/{cid}")
                    if r.status_code == 200:
                        body = r.json()
                        # trust only summary property for context
                        props = body.get('properties', {})
                        summary = props.get('summary')
                        if isinstance(summary, str) and len(summary) > 0:
                            parts.append(summary)
                except Exception as e:
                    logger.warn('kg_fetch_failed', cid=cid, error=str(e))
        context_text = '\n'.join(parts)

    prompt = (context_text + '\n' + req.prompt) if context_text else req.prompt
    redacted_prompt = redact(prompt)

    # call provider
    payload = {"prompt": redacted_prompt, "max_tokens": req.max_tokens}
    provider_resp = await call_provider(payload)
    text = provider_resp.get('text') or provider_resp.get('response') or ''
    latency_ms = int((time.time() - start) * 1000)

    REQUESTS.labels(endpoint=endpoint, status='ok').inc()
    DURATION.labels(endpoint=endpoint).observe(latency_ms / 1000.0)

    return CopilotResponse(response=redact(text), model=provider_resp.get('model', 'unknown'), latency_ms=latency_ms)

# OpenAPI security definition will indicate bearer auth
app.openapi_schema = None

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi = app.openapi()
    openapi['components']['securitySchemes'] = {
        'BearerAuth': {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT'
        }
    }
    # apply globally to endpoints that require auth
    for path, methods in openapi['paths'].items():
        for method_obj in methods.values():
            if path in ENDPOINT_ROLES:
                method_obj.setdefault('security', []).append({'BearerAuth': []})
    app.openapi_schema = openapi
    return app.openapi_schema

app.openapi = custom_openapi
