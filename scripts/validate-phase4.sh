#!/usr/bin/env bash
# PrintWatch — validação Fase 4 (Dashboard web via nginx :80)
# Uso: bash scripts/validate-phase4.sh [--quick]
# --quick: checks automáticos Wave 0 (<90s, sem interação humana)
#
# Variáveis de ambiente:
#   BASE_URL   URL base nginx (default: http://localhost)
#   COMPOSE_FILE   caminho do docker-compose.yml (default: ./docker-compose.yml)

set -euo pipefail

if [[ -n "${MSYSTEM:-}" ]] || [[ "$(uname -s 2>/dev/null)" == MINGW* ]]; then
  export MSYS_NO_PATHCONV=1
fi

QUICK=false
FAILURES=0
WARNINGS=0
BASE_URL="${BASE_URL:-http://localhost}"

usage() {
  echo "Uso: $0 [--quick]"
  echo "  --quick   checks automáticos Wave 0 (nginx + API proxy + Vitest)"
  echo ""
  echo "Variáveis:"
  echo "  BASE_URL   URL base nginx (default: $BASE_URL)"
}

parse_args() {
  if [[ $# -eq 0 ]]; then return; fi
  case "$1" in
    --quick) QUICK=true ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Argumento desconhecido: $1" >&2; usage; exit 1 ;;
  esac
}

pass() { echo "  [PASS] $*"; }
fail() { echo "  [FAIL] $*" >&2; FAILURES=$((FAILURES + 1)); }
warn() { echo "  [WARN] $*"; WARNINGS=$((WARNINGS + 1)); }

check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    pass "$label"
  else
    fail "$label"
  fi
}

check_http() {
  local label="$1"
  local expected_code="$2"
  local url="$3"
  local actual_code
  actual_code=$(curl -s -o /dev/null -w '%{http_code}' "$url")
  if [[ "$actual_code" == "$expected_code" ]]; then
    pass "$label"
  else
    fail "$label (esperado $expected_code, obtido $actual_code)"
  fi
}

parse_args "$@"

echo "PrintWatch — validate-phase4 ($([ "$QUICK" = "true" ] && echo "quick" || echo "full"))"
echo "BASE_URL=$BASE_URL"
echo

# ---------------------------------------------------------------------------
# 01 Container nginx up
# ---------------------------------------------------------------------------
if docker compose ps nginx 2>/dev/null | grep -qE "running|Up"; then
  pass "01 nginx container running"
else
  fail "01 nginx container não está running (docker compose up -d nginx)"
fi

# ---------------------------------------------------------------------------
# 02 SPA index — root element
# ---------------------------------------------------------------------------
check "02 GET / contém elemento root da SPA" \
  bash -c "curl -fsS '$BASE_URL/' | grep -qE 'id=[\"'\'']root[\"'\'']'"

# ---------------------------------------------------------------------------
# 03 GET /api/v1/health status=ok (via proxy nginx)
# ---------------------------------------------------------------------------
check "03 GET /api/v1/health status=ok" \
  bash -c "curl -fsS '$BASE_URL/api/v1/health' | python3 -c \"import json,sys; j=json.load(sys.stdin); assert j['status']=='ok'\""

# ---------------------------------------------------------------------------
# 04 GET /api/v1/health db_reachable=true
# ---------------------------------------------------------------------------
check "04 GET /api/v1/health db_reachable=true" \
  bash -c "curl -fsS '$BASE_URL/api/v1/health' | python3 -c \"import json,sys; j=json.load(sys.stdin); assert j['db_reachable']==True\""

# ---------------------------------------------------------------------------
# 05 GET /api/v1/jobs shape: items/total/page/size
# ---------------------------------------------------------------------------
check "05 GET /api/v1/jobs shape items/total/page/size" \
  bash -c "curl -fsS '$BASE_URL/api/v1/jobs?page=1&size=10' | python3 -c \"import json,sys; j=json.load(sys.stdin); assert {'items','total','page','size'} <= set(j.keys())\""

# ---------------------------------------------------------------------------
# 06 GET /api/v1/stats/summary shape: hoje/mes/total
# ---------------------------------------------------------------------------
check "06 GET /api/v1/stats/summary shape hoje/mes/total" \
  bash -c "curl -fsS '$BASE_URL/api/v1/stats/summary' | python3 -c \"
import json,sys
j=json.load(sys.stdin)
assert set(j.keys())=={'hoje','mes','total'}
for b in j.values():
    assert set(b.keys())=={'jobs','pages','top_users','top_printers'}
\""

# ---------------------------------------------------------------------------
# 07 GET /api/v1/printers lista JSON
# ---------------------------------------------------------------------------
check "07 GET /api/v1/printers lista JSON" \
  bash -c "curl -fsS '$BASE_URL/api/v1/printers' | python3 -c \"import json,sys; v=json.load(sys.stdin); assert isinstance(v, list)\""

# ---------------------------------------------------------------------------
# 08 CSV Content-Type + Content-Disposition via proxy
# ---------------------------------------------------------------------------
check "08 CSV Content-Type text/csv" \
  bash -c "curl -s -o /dev/null -D - '$BASE_URL/api/v1/export/csv' | grep -qi '^content-type: text/csv'"

check "08b CSV Content-Disposition attachment" \
  bash -c "curl -s -o /dev/null -D - '$BASE_URL/api/v1/export/csv' | grep -qi '^content-disposition: attachment'"

# ---------------------------------------------------------------------------
# 09 gzip em asset .js (cache immutable)
# ---------------------------------------------------------------------------
JS_PATH=$(curl -fsS "$BASE_URL/" | sed -n 's/.*src="\(\/assets\/[^"]*\.js\)".*/\1/p' | head -1)
if [[ -n "$JS_PATH" ]]; then
  if curl -sI "$BASE_URL$JS_PATH" | grep -qi 'content-encoding: gzip'; then
    pass "09 gzip em asset JS ($JS_PATH)"
  else
    warn "09 gzip não detectado em $JS_PATH (nginx gzip pode exigir Accept-Encoding)"
  fi
  if curl -sI "$BASE_URL$JS_PATH" | grep -qi 'cache-control:.*immutable'; then
    pass "09b Cache-Control immutable em asset JS"
  else
    warn "09b Cache-Control immutable ausente em $JS_PATH"
  fi
else
  warn "09 não foi possível extrair path de asset .js do index.html"
fi

# ---------------------------------------------------------------------------
# 10 Vitest Wave 0 (host)
# ---------------------------------------------------------------------------
if command -v npm >/dev/null 2>&1; then
  check "10 frontend Vitest (npm test -- --run)" \
    bash -c "cd frontend && npm test -- --run 2>&1"
else
  warn "10 npm não disponível — skip Vitest"
fi

# ---------------------------------------------------------------------------
# Resumo
# ---------------------------------------------------------------------------
echo
echo "Resumo: $FAILURES fail / $WARNINGS warn"

if [[ $FAILURES -gt 0 ]]; then
  echo
  echo "RESULTADO: FALHOU ($FAILURES check(s) falharam)"
  exit 1
fi

echo
echo "RESULTADO: OK — validate-phase4 passou"
exit 0
