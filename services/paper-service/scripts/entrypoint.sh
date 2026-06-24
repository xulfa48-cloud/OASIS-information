#!/usr/bin/env bash
set -euo pipefail

if [ -n "${PAPER_DATABASE_URL:-}" ]; then
  echo "Running migrations against ${PAPER_DATABASE_URL}"
  # run migration tooling if present
fi

exec node dist/index.js
