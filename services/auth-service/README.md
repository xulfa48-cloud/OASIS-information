# Auth Service

This service implements authentication and authorization primitives for the OASIS platform. It is responsible for:

- User credential storage and verification
- JWT issuance and rotation
- Session and refresh token lifecycle
- Role-based claims for internal services
- Exposing a small secure API used by the gateway and other services

Architecture overview

- Written in Go following a layered internal package design (config → server → handlers → storage).
- Persistent storage: PostgreSQL (primary), Redis for short-lived token/session storage and rate limiting.
- Exposes HTTP API protected with bearer JWTs for downstream services and JSON endpoints for client sign-in flows.
- Publishes events to a message bus (Kafka) for user lifecycle events: user.created, user.updated, user.deleted, token.revoked.

API contract (HTTP JSON)

Base path: /api/v1

Endpoints:
- POST /api/v1/auth/login
  Request: { "email": "user@example.com", "password": "secret" }
  Response: { "access_token": "<jwt>", "refresh_token": "<token>", "expires_in": 3600 }

- POST /api/v1/auth/refresh
  Request: { "refresh_token": "<token>" }
  Response: { "access_token": "<jwt>", "refresh_token": "<token>", "expires_in": 3600 }

- POST /api/v1/auth/logout
  Request: { "refresh_token": "<token>" }
  Response: 204 No Content

- GET /api/v1/health
  Response: { "status": "ok" }

Environment variables

- AUTH_PORT (default: 8080)
- AUTH_ENV (production|staging|development)
- AUTH_DATABASE_URL (postgres://user:pass@host:5432/authdb)
- AUTH_REDIS_URL (redis://host:6379/0)
- AUTH_JWT_PRIVATE_KEY (PEM, for signing — production should use KMS/Secrets Manager)
- AUTH_JWT_ISSUER (issuer claim)
- AUTH_JWT_EXP_SECONDS (default: 3600)
- AUTH_LOG_LEVEL (info|debug|warn|error)
- AUTH_KAFKA_BROKERS (comma-separated list)

Database schema

See migrations/001_init.sql for the canonical schema. In summary:
- users: id (uuid pk), email (unique), password_hash, roles(jsonb), created_at, updated_at, disabled
- refresh_tokens: id, user_id, token_hash, issued_at, expires_at, revoked

Events

- user.created {user_id, email, created_at}
- user.updated {user_id, changes, updated_at}
- token.revoked {token_id, user_id, reason}

Health checks & metrics

- /api/v1/health — liveness
- /api/v1/ready — readiness (checks DB and Redis connectivity)
- Prometheus metrics exposed at /metrics
  - oasis_auth_requests_total (labels: path, method, status)
  - oasis_auth_request_duration_seconds_bucket
  - oasis_auth_active_sessions

Operational notes

- Secrets must be injected via the platform (Vault / AWS Secrets Manager). Never store private keys in plaintext in the repo.
- Scale: stateless application instances with shared PostgreSQL and Redis. Use connection pooling and health-based autoscaling.

Run locally

1. Copy env.example to .env and set values
2. Start local dependencies (Postgres / Redis)
3. go build ./...
4. ./auth-service

