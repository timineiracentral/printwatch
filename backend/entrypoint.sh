#!/bin/bash
set -euo pipefail

export DB_PATH="${DB_PATH:-/app/data/printwatch.db}"
export LOG_PATH="${LOG_PATH:-/var/log/cups/page_log}"
export LOG_RETENTION_DAYS="${LOG_RETENTION_DAYS:-90}"

mkdir -p "$(dirname "$DB_PATH")"

# create_all para tabelas novas; alembic altera print_jobs existente (printer_id, etc.)
python -c "import app.db.session"  # noqa: F401

if [[ -f /app/scripts/ensure_db_schema.py ]]; then
  python /app/scripts/ensure_db_schema.py
elif [[ -f alembic.ini ]]; then
  alembic -c /app/alembic.ini upgrade head
else
  echo "WARN: alembic.ini missing — schema may be stale on existing DB volumes" >&2
fi

if [[ -f "$DB_PATH" ]]; then
  chmod 600 "$DB_PATH"
fi

if [[ "${SIMPRESS_ENABLED:-true}" =~ ^(1|true|yes)$ ]]; then
  mkdir -p "$(dirname "${SIMPRESS_DB_PATH:-/app/data/simpress.db}")"
  alembic -c /app/alembic_simpress.ini upgrade head
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
