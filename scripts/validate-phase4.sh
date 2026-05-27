#!/usr/bin/env bash
# PrintWatch — validação Fase 4 (Dashboard web via nginx :80)
# Uso: bash scripts/validate-phase4.sh [--quick]
# --quick: checks automáticos (<90s, sem interação humana)
# (sem flag): suite completa + checkpoint humano ROADMAP critérios 1-5 (D-67)
#
# Produção: dashboard em http://<VM_HOST> (nginx :80, same-origin /api/v1).
# Dev local: Vite em http://localhost:5173 com proxy /api → backend :8000;
#   CORS ainda relevante para dev direto contra backend ou preflight via nginx.
#
# Variáveis de ambiente:
#   BASE_URL       URL base nginx (default: http://localhost)
#   BACKEND_URL    URL backend direto para CORS dev (default: http://localhost:8000)
#   COMPOSE_FILE   caminho do docker-compose.yml (default: ./docker-compose.yml)

set -euo pipefail

if [[ -n "${MSYSTEM:-}" ]] || [[ "$(uname -s 2>/dev/null)" == MINGW* ]]; then
  export MSYS_NO_PATHCONV=1
fi

QUICK=false
FAILURES=0
WARNINGS=0
BASE_URL="${BASE_URL:-http://localhost}"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"

usage() {
  echo "Uso: $0 [--quick]"
  echo "  --quick   checks automáticos (nginx + API proxy + Vitest + export)"
  echo "  (sem flag) Suite completa + checkpoint humano ROADMAP crit. 1-5"
  echo ""
  echo "Variáveis:"
  echo "  BASE_URL      URL base nginx (default: $BASE_URL)"
  echo "  BACKEND_URL   URL backend para CORS dev (default: $BACKEND_URL)"
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

parse_args "$@"

echo "PrintWatch — validate-phase4 ($([ "$QUICK" = "true" ] && echo "quick" || echo "full"))"
echo "BASE_URL=$BASE_URL"
echo "BACKEND_URL=$BACKEND_URL (CORS dev)"
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
# 09 CSV BOM UTF-8 (EF BB BF) + separador ; + header PT-BR
# ---------------------------------------------------------------------------
TMPCSV=$(mktemp /tmp/printwatch_p4_XXXXXX.csv)
curl -fsS "$BASE_URL/api/v1/export/csv" -o "$TMPCSV"
if command -v xxd >/dev/null 2>&1; then
  check "09 CSV BOM UTF-8 (ef bb bf)" \
    bash -c "xxd '$TMPCSV' | head -1 | grep -q 'efbb bf\|ef bb bf'"
else
  check "09 CSV BOM UTF-8 (python)" \
    bash -c "python3 -c \"
with open('$TMPCSV', 'rb') as f:
    assert f.read(3) == b'\\xef\\xbb\\xbf', 'BOM ausente'
\""
fi

check "10 CSV header com separador ';' e colunas PT-BR" \
  bash -c "python3 -c \"
import codecs
with open('$TMPCSV', encoding='utf-8-sig') as f:
    header = f.readline().strip()
assert ';' in header, f'Separador não é ;: {header}'
assert 'Usuário' in header or 'Usuario' in header, f'Header sem Usuário: {header}'
\""
rm -f "$TMPCSV"

# ---------------------------------------------------------------------------
# 11 /jobs?date_from > date_to → 422
# ---------------------------------------------------------------------------
check "11 /jobs date_from > date_to → 422" \
  bash -c "[ \"\$(curl -s -o /dev/null -w '%{http_code}' '$BASE_URL/api/v1/jobs?date_from=2026-12-31&date_to=2026-01-01')\" = '422' ]"

# ---------------------------------------------------------------------------
# 12 /jobs?size=999 → 422
# ---------------------------------------------------------------------------
check "12 /jobs size=999 → 422" \
  bash -c "[ \"\$(curl -s -o /dev/null -w '%{http_code}' '$BASE_URL/api/v1/jobs?size=999')\" = '422' ]"

# ---------------------------------------------------------------------------
# 13 CORS preflight origem permitida (dev Vite :5173 — backend direto)
# ---------------------------------------------------------------------------
if curl -sI -X OPTIONS \
  -H 'Origin: http://localhost:5173' \
  -H 'Access-Control-Request-Method: GET' \
  "$BACKEND_URL/api/v1/jobs" 2>/dev/null | grep -qi 'access-control-allow-origin: http://localhost:5173'; then
  pass "13 CORS allow-origin para localhost:5173 (BACKEND_URL)"
else
  warn "13 CORS localhost:5173 — backend indisponível ou ALLOWED_ORIGINS sem :5173 (dev apenas)"
fi

# ---------------------------------------------------------------------------
# 14 CORS bloqueia evil.com
# ---------------------------------------------------------------------------
if curl -sI -X OPTIONS \
  -H 'Origin: http://evil.com' \
  -H 'Access-Control-Request-Method: GET' \
  "$BACKEND_URL/api/v1/jobs" 2>/dev/null | grep -qi 'access-control-allow-origin: http://evil.com'; then
  fail "14 CORS não deve permitir evil.com"
else
  pass "14 CORS bloqueia evil.com"
fi

# ---------------------------------------------------------------------------
# 15 GET /jobs tempo de resposta (hint DASH-06)
# ---------------------------------------------------------------------------
JOBS_TIME=$(curl -s -o /dev/null -w '%{time_total}' "$BASE_URL/api/v1/jobs?page=1&size=50" 2>/dev/null || echo "999")
if python3 -c "import sys; sys.exit(0 if float('$JOBS_TIME') < 0.5 else 1)" 2>/dev/null; then
  pass "15 GET /jobs time_total=${JOBS_TIME}s (<0.5s)"
else
  warn "15 GET /jobs time_total=${JOBS_TIME}s — acima de 0.5s (DB grande ou host lento; DASH-06 hint)"
fi

# ---------------------------------------------------------------------------
# 16 Vitest (host)
# ---------------------------------------------------------------------------
if command -v npm >/dev/null 2>&1; then
  check "16 frontend Vitest (npm test -- --run)" \
    bash -c "cd frontend && npm test -- --run 2>&1"
else
  warn "16 npm não disponível — skip Vitest"
fi

# ---------------------------------------------------------------------------
# Resumo automático
# ---------------------------------------------------------------------------
echo
echo "Resumo (auto): $FAILURES fail / $WARNINGS warn"

# ---------------------------------------------------------------------------
# Modo completo: checkpoint humano ROADMAP critérios 1-5 (D-67)
# ---------------------------------------------------------------------------
if [[ "$QUICK" == "false" ]]; then
  echo
  echo "═══════════════════════════════════════════════════════"
  echo "  17. CHECKPOINT HUMANO — ROADMAP Fase 4 critérios 1-5"
  echo "═══════════════════════════════════════════════════════"
  echo
  echo "Pré-requisito: checks automáticos acima verdes."
  echo "Validar em browser: $BASE_URL (ou http://<VM_HOST>)"
  echo
  echo "  1. DASH-06: Hard refresh; DevTools — paint cards+tabela < 2s (rede local)"
  echo "  2. DASH-02: Cards 'Jobs hoje' / 'Páginas hoje' vs curl $BASE_URL/api/v1/stats/summary"
  echo "  3. DASH-04: Filtro usuário + impressora; tabela e URL refletem params"
  echo "  4. DASH-05: Busca parcial por nome de arquivo retorna matches corretos"
  echo "  5. EXPORT-01: Exportar CSV com filtros; Excel pt-BR — separador ;, acentos OK"
  echo
  echo "Registrar evidência em .planning/phases/04-dashboard-web/04-VERIFICATION.md"
  echo
  read -r -p "Checkpoint ROADMAP crit. 1-5 aprovado? [y/N]: " ans
  if [[ "${ans,,}" == "y" ]]; then
    pass "17 checkpoint humano aprovado (operador confirmou critérios ROADMAP)"
  else
    fail "17 checkpoint humano NÃO aprovado — documentar em 04-VERIFICATION.md"
  fi
fi

if [[ $FAILURES -gt 0 ]]; then
  echo
  echo "RESULTADO: FALHOU ($FAILURES check(s) falharam)"
  exit 1
fi

echo
echo "RESULTADO: OK — validate-phase4 passou"
exit 0
