#!/usr/bin/env bash
set -euo pipefail
cd ~/printwatch

echo "=== 1 GIT ==="
git log -1 --oneline
git status -sb | head -3

echo "=== 2 DOCKER ==="
docker compose ps

echo "=== 3 ALEMBIC ==="
docker compose exec -T -w /app -e DB_PATH=/app/data/printwatch.db backend alembic current

echo "=== 4 DB SCHEMA ==="
docker compose exec -T backend python <<'PY'
import sqlite3
c = sqlite3.connect("/app/data/printwatch.db")
cols = [r[1] for r in c.execute("PRAGMA table_info(print_jobs)")]
need = ["printer_id", "color_mode", "color_mode_source"]
for n in need:
    print(f"  print_jobs.{n}: {'OK' if n in cols else 'MISSING'}")
tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print(f"  cost_rates table: {'OK' if 'cost_rates' in tables else 'MISSING'}")
print(f"  user_printer_access: {'OK' if 'user_printer_access' in tables else 'MISSING'}")
PY

echo "=== 5 COLOR_MODE STATS ==="
docker compose exec -T backend python <<'PY'
import sqlite3
c = sqlite3.connect("/app/data/printwatch.db")
rows = c.execute(
    "SELECT COALESCE(color_mode,'NULL'), COUNT(*) FROM print_jobs GROUP BY 1 ORDER BY 2 DESC"
).fetchall()
print("  distribution:", rows)
recent = c.execute(
    "SELECT printer, color_mode, timestamp FROM print_jobs ORDER BY timestamp DESC LIMIT 5"
).fetchall()
print("  recent jobs:")
for r in recent:
    print("   ", r)
PY

echo "=== 6 API ==="
code=$(curl -s -o /tmp/pw_jobs.json -w "%{http_code}" "http://127.0.0.1/api/v1/jobs?page=1&size=1")
echo "  GET /api/v1/jobs -> HTTP $code"
if [ "$code" = "200" ]; then
  python3 -c "import json; j=json.load(open('/tmp/pw_jobs.json')); i=j.get('items',[{}])[0]; print('  sample keys:', sorted(i.keys())[:12], '...')"
else
  head -c 200 /tmp/pw_jobs.json 2>/dev/null; echo
fi

health=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1/api/v1/health")
echo "  GET /api/v1/health -> HTTP $health"

echo "=== 7 CUPS QUEUES ==="
docker compose exec -T cups lpstat -p 2>/dev/null | head -10 || echo "  (lpstat unavailable)"

echo "=== DONE ==="
