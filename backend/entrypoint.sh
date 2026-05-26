#!/bin/bash
set -euo pipefail

export DB_PATH="${DB_PATH:-/app/data/printwatch.db}"
export LOG_PATH="${LOG_PATH:-/var/log/cups/page_log}"
export LOG_RETENTION_DAYS="${LOG_RETENTION_DAYS:-90}"

mkdir -p "$(dirname "$DB_PATH")"

if [[ -f "$DB_PATH" ]]; then
  chmod 600 "$DB_PATH"
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
