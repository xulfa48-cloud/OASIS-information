#!/usr/bin/env bash
set -euo pipefail

# Entrypoint for the auth-service container

# Optional: wait for the database to become available
if [ -n "${AUTH_DATABASE_URL:-}" ]; then
  echo "Waiting for database to be available at ${AUTH_DATABASE_URL}"
  # It's recommended the container platform handles readiness; here we just sleep a short time
  sleep 2
fi

# Run migrations if migrator is available (expects migrate CLI present in image)
if command -v migrate >/dev/null 2>&1; then
  echo "Running database migrations"
  migrate -path /migrations -database "${AUTH_DATABASE_URL}" up || true
fi

# Start the service binary
exec /bin/auth-service "$@"
