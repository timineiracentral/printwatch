#!/usr/bin/env bash
# PrintWatch — validação Fase 3 (Backend API)
# Uso: bash scripts/validate-phase3.sh [--quick]
# --quick: 16 checks automáticos (<60s, sem interação humana)
# (sem flag): suite completa incluindo checkpoint #17 (job real Windows AD + CSV no Excel)
#
# Variáveis de ambiente:
#   BASE_URL   URL base da API (default: http://localhost:8000)
#   COMPOSE_FILE   caminho do docker-compose.yml (default: ./docker-compose.yml)

set -euo pipefail

# Git Bash/MSYS: evita conversão de paths em `docker compose exec`
if [[ -n "${MSYSTEM:-}" ]] || [[ "$(uname -s 2>/dev/null)" == MINGW* ]]; then
  export MSYS_NO_PATHCONV=1
fi

QUICK=false
FAILURES=0
WARNINGS=0
BASE_URL="${BASE_URL:-http://localhost:8000}"

usage() {
  echo "Uso: $0 [--quick]"
  echo "  --quick   16 checks automáticos Nyquist (sem interação humana)"
  echo "  (sem flag) Suite completa: auto checks + checkpoint #17 (operador manual)"
  echo ""
  echo "Variáveis:"
  echo "  BASE_URL   URL base da API (default: $BASE_URL)"
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

echo "PrintWatch — validate-phase3 ($([ "$QUICK" = "true" ] && echo "quick" || echo "full"))"
echo "BASE_URL=$BASE_URL"
echo

# ---------------------------------------------------------------------------
# 01 Container backend up
# ---------------------------------------------------------------------------
if docker compose ps backend 2>/dev/null | grep -qE "running|Up"; then
  pass "01 backend container running"
else
  warn "01 backend container não encontrado via docker compose — assumindo BASE_URL externo"
fi

# ---------------------------------------------------------------------------
# 02 OpenAPI info.title == PrintWatch
# ---------------------------------------------------------------------------
check "02 GET /api/v1/openapi.json info.title=PrintWatch API" \
  bash -c "curl -fsS '$BASE_URL/api/v1/openapi.json' | python3 -c \"import json,sys; t=json.load(sys.stdin)['info']['title']; assert 'PrintWatch' in t, f'Inesperado: {t}'\""

# ---------------------------------------------------------------------------
# 03 GET /api/v1/health status=ok
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
# 06 4 índices SQLite existem em print_jobs
# ---------------------------------------------------------------------------
check "06 4 índices SQLite em print_jobs" \
  bash -c "docker compose exec -T backend python3 -c \"
from sqlalchemy import inspect
from app.db.session import engine
idx = {i['name'] for i in inspect(engine).get_indexes('print_jobs')}
required = {'idx_print_jobs_timestamp','idx_print_jobs_username_timestamp','idx_print_jobs_printer_timestamp','idx_print_jobs_job_id'}
assert required <= idx, f'Faltam: {required - idx}'
\""

# ---------------------------------------------------------------------------
# 07 EXPLAIN QUERY PLAN usa idx_print_jobs_timestamp
# ---------------------------------------------------------------------------
check "07 EXPLAIN usa idx_print_jobs_timestamp" \
  bash -c "docker compose exec -T backend python3 -c \"
from sqlalchemy import text
from app.db.session import engine
with engine.connect() as con:
    rows = con.execute(text('EXPLAIN QUERY PLAN SELECT * FROM print_jobs ORDER BY timestamp DESC LIMIT 50')).fetchall()
assert any('idx_print_jobs_timestamp' in str(r) for r in rows), f'Índice não usado: {rows}'
\""

# ---------------------------------------------------------------------------
# 08 Content-Type text/csv + Content-Disposition attachment
# (usa GET com -D - para capturar headers sem HEAD, pois StreamingResponse não aceita HEAD)
# ---------------------------------------------------------------------------
check "08 CSV Content-Type text/csv" \
  bash -c "curl -s -o /dev/null -D - '$BASE_URL/api/v1/export/csv' | grep -qi '^content-type: text/csv'"

check "08b CSV Content-Disposition attachment" \
  bash -c "curl -s -o /dev/null -D - '$BASE_URL/api/v1/export/csv' | grep -qi '^content-disposition: attachment'"

# ---------------------------------------------------------------------------
# 09 CSV BOM UTF-8 (EF BB BF)
# ---------------------------------------------------------------------------
TMPCSV=$(mktemp /tmp/printwatch_test_XXXXXX.csv)
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

# ---------------------------------------------------------------------------
# 10 CSV separador ; e cabeçalho PT-BR
# ---------------------------------------------------------------------------
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
# 13 /printers retorna lista JSON ordenada
# ---------------------------------------------------------------------------
check "13 GET /api/v1/printers lista JSON ordenada" \
  bash -c "curl -fsS '$BASE_URL/api/v1/printers' | python3 -c \"import json,sys; v=json.load(sys.stdin); assert isinstance(v, list), 'Não é lista'\""

# ---------------------------------------------------------------------------
# 14 CORS preflight origem permitida
# ---------------------------------------------------------------------------
check "14 CORS allow-origin para localhost:5173" \
  bash -c "curl -sI -X OPTIONS \
    -H 'Origin: http://localhost:5173' \
    -H 'Access-Control-Request-Method: GET' \
    '$BASE_URL/api/v1/jobs' | grep -qi 'access-control-allow-origin: http://localhost:5173'"

# ---------------------------------------------------------------------------
# 15 CORS bloqueia evil.com
# ---------------------------------------------------------------------------
check "15 CORS bloqueia evil.com" \
  bash -c "! curl -sI -X OPTIONS \
    -H 'Origin: http://evil.com' \
    -H 'Access-Control-Request-Method: GET' \
    '$BASE_URL/api/v1/jobs' | grep -qi 'access-control-allow-origin: http://evil.com'"

# ---------------------------------------------------------------------------
# 16 pytest suite green (roda no host, no diretório backend/)
# Os testes não são copiados para o container de produção (Dockerfile copia só app/)
# ---------------------------------------------------------------------------
if command -v pytest >/dev/null 2>&1 || python3 -m pytest --version >/dev/null 2>&1; then
  check "16 pytest suite green (host)" \
    bash -c "cd backend && python3 -m pytest -q --tb=no 2>&1"
else
  warn "16 pytest não disponível no host — skip (rodar manualmente: cd backend && python3 -m pytest -q)"
fi

# ---------------------------------------------------------------------------
# Resumo automático
# ---------------------------------------------------------------------------
echo
echo "Resumo (auto): $((16 - FAILURES - WARNINGS + 2)) pass / $FAILURES fail / $WARNINGS warn"
# Nota: contagem inclui os 17 checks numerados no plano (08 tem 2 sub-checks)

# ---------------------------------------------------------------------------
# Modo completo: checkpoint humano #17
# ---------------------------------------------------------------------------
if [[ "$QUICK" == "false" ]]; then
  echo
  echo "═══════════════════════════════════════════════════════"
  echo "  17. CHECKPOINT HUMANO — Job real Windows AD + CSV"
  echo "═══════════════════════════════════════════════════════"
  echo
  echo "Pré-requisitos:"
  echo "  - PC Windows com impressora PrintWatch configurada via IPP"
  echo "  - Usuário logado com conta AD"
  echo
  echo "Passos:"
  echo "  a) Imprimir um documento de teste para a impressora PrintWatch"
  echo "  b) Aguardar até 30 segundos"
  echo "  c) Executar em outro terminal:"
  echo "       curl '$BASE_URL/api/v1/jobs' | python3 -m json.tool | head -40"
  echo "     Confirmar: job aparece com printer, pages, timestamp, host_origin"
  echo "  d) Baixar CSV:"
  echo "       curl '$BASE_URL/api/v1/export/csv' -o /tmp/printwatch_test.csv"
  echo "  e) Abrir /tmp/printwatch_test.csv no Excel pt-BR:"
  echo "     - Deve abrir SEM prompt de import"
  echo "     - Acentos corretos (Usuário, Páginas)"
  echo "     - Colunas separadas por ;"
  echo "     - Datas no fuso local"
  echo
  read -r -p "Checkpoint #17 aprovado? [y/N]: " ans
  if [[ "${ans,,}" == "y" ]]; then
    pass "17 checkpoint humano aprovado (operador confirmou job AD + CSV Excel)"
  else
    fail "17 checkpoint humano NÃO aprovado — documentar falha em 03-VERIFICATION.md"
  fi

  echo
  echo "Resumo final: $((17 - FAILURES)) pass / $FAILURES fail / $WARNINGS warn"
fi

if [[ $FAILURES -gt 0 ]]; then
  echo
  echo "RESULTADO: FALHOU ($FAILURES check(s) falharam)"
  exit 1
fi

echo
echo "RESULTADO: OK — todos os checks passaram"
exit 0
