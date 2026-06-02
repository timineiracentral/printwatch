#!/usr/bin/env bash
set -euo pipefail
cd ~/printwatch

docker compose exec -T backend python <<'PY'
import sqlite3
c = sqlite3.connect("/app/data/printwatch.db")
cols = [r[1] for r in c.execute("PRAGMA table_info(print_jobs)")]
if "color_mode_source" in cols:
    print("color_mode_source already exists")
else:
    c.execute("ALTER TABLE print_jobs ADD COLUMN color_mode_source VARCHAR(20)")
    c.commit()
    print("ADDED color_mode_source")
PY

docker compose restart backend
sleep 3
code=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1/api/v1/jobs?page=1&size=1")
echo "GET /api/v1/jobs -> HTTP $code"
