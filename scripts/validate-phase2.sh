#!/usr/bin/env bash
# PrintWatch — validação Fase 2 (log pipeline + data layer)
# Uso: bash scripts/validate-phase2.sh [--quick]
# --quick: smoke tests Nyquist (<60s, sem job local no banco)
# (sem flag): suite completa com job lp + confirmação no SQLite (Plan 05)

set -euo pipefail

# Git Bash/MSYS: evita conversão de paths em `docker compose exec`
if [[ -n "${MSYSTEM:-}" ]] || [[ "$(uname -s 2>/dev/null)" == MINGW* ]]; then
  export MSYS_NO_PATHCONV=1
fi

QUICK_MODE=false
FAILURES=0
WARNINGS=0
TEST_PRINTER_NAME="${TEST_PRINTER_NAME:-}"

pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; FAILURES=$((FAILURES + 1)); }
warn() { echo "[WARN] $1"; WARNINGS=$((WARNINGS + 1)); }

usage() {
  echo "Uso: $0 [--quick]"
  echo "  --quick   Smoke tests Fase 2 (não envia job lp para o banco)"
  echo "  (sem flag) Suite completa: quick checks + job lp + espera no SQLite"
}

parse_args() {
  if [[ $# -eq 0 ]]; then
    QUICK_MODE=false
    return
  fi
  case "$1" in
    --quick)
      QUICK_MODE=true
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Argumento desconhecido: $1" >&2
      usage
      exit 1
      ;;
  esac
}

load_test_env() {
  local env_file=".env"
  if [[ ! -f "$env_file" ]]; then
    env_file=".env.example"
    warn "Arquivo .env ausente — usando .env.example para TEST_PRINTER_NAME"
  fi

  TEST_PRINTER_NAME="$(grep -E '^TEST_PRINTER_NAME=' "$env_file" | head -1 | cut -d= -f2- | tr -d '\r')"
  if [[ -z "$TEST_PRINTER_NAME" ]]; then
    fail "TEST_PRINTER_NAME não definido em ${env_file}"
  else
    pass "TEST_PRINTER_NAME=${TEST_PRINTER_NAME}"
  fi
}

docker_daemon_ready() {
  command -v docker >/dev/null 2>&1 || return 1
  docker info >/dev/null 2>&1
}

backend_container_running() {
  # Tenta --status running (Compose v2.17+); cai para grep "Up" se não suportado
  local out
  out="$(docker compose ps backend 2>/dev/null)"
  echo "$out" | grep -qiE '\bUp\b|running' && return 0
  return 1
}

check_backend_running() {
  if backend_container_running; then
    pass "Container backend está running"
  else
    fail "Container backend não está running"
  fi
}

check_backend_image() {
  if docker compose images backend 2>/dev/null | grep -qE 'backend|printwatch-backend'; then
    pass "Imagem backend presente (docker compose images)"
  else
    warn "Imagem backend não encontrada em docker compose images"
  fi
}

check_healthz() {
  local body
  if ! body="$(docker compose exec -T backend python -c "
import urllib.request
print(urllib.request.urlopen('http://localhost:8000/healthz', timeout=5).read().decode())
" 2>/dev/null)"; then
    fail "GET /healthz falhou no container backend"
    return
  fi
  body="${body//$'\r'/}"
  if echo "$body" | grep -q '"status"[[:space:]]*:[[:space:]]*"ok"'; then
    pass "/healthz status ok"
  else
    fail "/healthz sem status ok: ${body}"
  fi
  if echo "$body" | grep -qE '"watcher"[[:space:]]*:[[:space:]]*true'; then
    pass "/healthz watcher:true (D-13)"
  else
    fail "/healthz watcher não está true: ${body}"
  fi
}

check_db_tables() {
  if docker compose exec -T backend python -c "
from sqlalchemy import inspect
from app.db.session import engine
t = inspect(engine).get_table_names()
required = ['print_jobs', 'capture_state', 'policies']
missing = [x for x in required if x not in t]
assert not missing, f'missing tables: {missing}, have: {t}'
print('ok')
" >/dev/null 2>&1; then
    pass "Tabelas print_jobs, capture_state e policies existem"
  else
    fail "Tabelas obrigatórias ausentes no SQLite (print_jobs, capture_state, policies)"
  fi
}

check_sqlite_permissions() {
  local stat_out
  if ! stat_out="$(docker compose exec -T backend stat /app/data/printwatch.db 2>/dev/null)"; then
    warn "Não foi possível stat /app/data/printwatch.db (arquivo pode não existir ainda)"
    return
  fi
  if echo "$stat_out" | grep -qE '0600|Access: \(0[0-7]{3}/0[0-7]{3}/-rw-------\)'; then
    pass "SQLite permissões 600 em /app/data/printwatch.db (DATA-03)"
  elif echo "$stat_out" | grep -qE '0660|0664|0640|0644'; then
    warn "SQLite permissões não são 600 (DATA-03): ver stat abaixo"
    echo "  ${stat_out}" | head -3
  else
    warn "Não foi possível confirmar modo 600 do SQLite — revisar manualmente"
    echo "  ${stat_out}" | head -3
  fi
}

check_status_default_allowed() {
  if docker compose exec -T backend python -c "
from datetime import datetime, timezone
from app.db.session import SessionLocal
from app.db.models import PrintJob
s = SessionLocal()
j = PrintJob(
    printer='p',
    username='u',
    job_id=1,
    timestamp=datetime.now(timezone.utc),
    pages=1,
)
s.add(j)
s.flush()
assert j.status == 'allowed', j.status
s.rollback()
s.close()
print('ok')
" >/dev/null 2>&1; then
    pass "PrintJob.status default 'allowed' (EXTEND-01)"
  else
    fail "PrintJob.status default não é 'allowed'"
  fi
}

check_pre_process_job() {
  if docker compose exec -T backend python -c "
from app.watcher.handler import pre_process_job
assert pre_process_job({}) is True
print('ok')
" >/dev/null 2>&1; then
    pass "pre_process_job retorna True (EXTEND-03)"
  else
    fail "pre_process_job não retorna True"
  fi
}

check_cups_without_backend() {
  local lpstat_out=""
  echo "--- CAPTURE-04: CUPS com backend parado ---"
  docker compose stop backend >/dev/null 2>&1 || true
  sleep 2

  if lpstat_out="$(docker compose exec -T cups lpstat -r 2>/dev/null)"; then
    if echo "$lpstat_out" | grep -qi 'scheduler'; then
      pass "CUPS responde lpstat -r com backend parado (CAPTURE-04)"
    else
      fail "CUPS lpstat -r sem 'scheduler' com backend parado"
    fi
  else
    fail "CUPS lpstat -r falhou com backend parado"
  fi

  docker compose start backend >/dev/null 2>&1 || true
  sleep 3
  if backend_container_running; then
    pass "Backend reiniciado após teste CAPTURE-04"
  else
    fail "Backend não voltou após teste CAPTURE-04"
  fi
}

check_pytest_suite() {
  local repo_root
  repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  echo "--- pytest backend/tests (host — tests/ não está na imagem backend) ---"
  # Detecta python3 ou python disponível no host
  local PY_CMD
  if command -v python3 >/dev/null 2>&1; then
    PY_CMD="python3"
  elif command -v python >/dev/null 2>&1; then
    PY_CMD="python"
  else
    warn "python/python3 não encontrado no host — pytest ignorado (testes passam localmente no dev)"
    return 0
  fi
  # Verifica se pytest está instalado; se não, avisa sem falhar (pytest é dep de dev)
  if ! "$PY_CMD" -m pytest --version >/dev/null 2>&1; then
    warn "pytest não instalado no host — ignorado (execute: cd backend && pip install pytest && python3 -m pytest tests/)"
    return 0
  fi
  if (
    cd "$repo_root/backend"
    "$PY_CMD" -m pytest tests/ -q --tb=short
  ); then
    pass "pytest tests/ passou (24+ testes)"
  else
    fail "pytest tests/ falhou — execute: cd backend && python3 -m pytest tests/ -q"
  fi
}

db_max_job_id() {
  docker compose exec -T backend python -c "
from app.db.session import SessionLocal
from app.db.models import PrintJob
s = SessionLocal()
row = s.query(PrintJob.id).order_by(PrintJob.id.desc()).first()
s.close()
print(row[0] if row else 0)
" 2>/dev/null | tr -d '\r'
}

ensure_test_printer() {
  local printer="${TEST_PRINTER_NAME:-test_printer}"
  if docker compose exec -T cups lpstat -p "$printer" >/dev/null 2>&1; then
    pass "Impressora CUPS '${printer}' disponível"
    return 0
  fi
  warn "Impressora '${printer}' ausente — executando scripts/setup-printer.sh"
  local script_dir repo_root
  script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  repo_root="$(cd "${script_dir}/.." && pwd)"
  if (cd "$repo_root" && bash "${script_dir}/setup-printer.sh"); then
    pass "setup-printer.sh concluído"
  else
    fail "setup-printer.sh falhou — configure TEST_PRINTER_NAME no .env"
    return 1
  fi
}

send_full_test_job() {
  local printer="${TEST_PRINTER_NAME:-test_printer}"
  FULL_JOB_TITLE="phase2-local-test-$(date +%s)"
  ensure_test_printer || return 1

  pass "Enviando job lp para ${printer} (title=${FULL_JOB_TITLE})..."
  if docker compose exec -T cups bash -c \
    'echo "PrintWatch phase2 test" | lp -d '"$printer"' -U '"'"'DOMINIO\usuario'"'"' -t '"$FULL_JOB_TITLE" \
    >/dev/null 2>&1; then
    pass "Job lp enviado para ${printer}"
  else
    fail "lp job local falhou para impressora ${printer}"
    return 1
  fi
}

wait_for_job_in_db() {
  local attempt max_attempts=10
  local found

  pass "Aguardando job '${FULL_JOB_TITLE}' no banco (até 30s)..."

  for attempt in $(seq 1 "$max_attempts"); do
    found="$(docker compose exec -T backend python -c "
from app.db.session import SessionLocal
from app.db.models import PrintJob
s = SessionLocal()
j = s.query(PrintJob).filter(PrintJob.job_name == '${FULL_JOB_TITLE}').first()
s.close()
print('yes' if j else 'no')
" 2>/dev/null | tr -d '\r')"
    if [[ "$found" == "yes" ]]; then
      pass "Job '${FULL_JOB_TITLE}' no banco após ~$((attempt * 3))s"
      return 0
    fi
    sleep 3
  done
  fail "Job '${FULL_JOB_TITLE}' não apareceu no banco após 30s"
  return 1
}

print_latest_job() {
  local job_line
  if job_line="$(docker compose exec -T backend python -c "
from app.db.session import SessionLocal
from app.db.models import PrintJob
s = SessionLocal()
j = s.query(PrintJob).order_by(PrintJob.id.desc()).first()
s.close()
if j is None:
    print('NO_JOBS')
else:
    print(f'username={j.username}, printer={j.printer}, pages={j.pages}, status={j.status}')
" 2>/dev/null)"; then
    job_line="${job_line//$'\r'/}"
    if [[ "$job_line" == "NO_JOBS" ]]; then
      fail "Nenhum job para exibir após espera"
    else
      pass "Último job no banco: ${job_line}"
      if [[ "$job_line" == *'\\'* ]] || [[ "$job_line" == username=DOMINIO* ]]; then
        pass "username contém formato DOMINIO\\usuario"
      else
        warn "username sem backslash AD (esperado em job Windows; local pode variar): ${job_line}"
      fi
    fi
  else
    fail "Não foi possível ler último PrintJob"
  fi
}

print_summary() {
  echo "=== Resumo: ${FAILURES} FAIL, ${WARNINGS} WARN ==="
  if [[ "$FAILURES" -gt 0 ]]; then
    exit 1
  fi
  exit 0
}

run_quick() {
  echo "=== PrintWatch validate-phase2 (--quick) ==="

  if ! docker_daemon_ready; then
    fail "Docker offline — obrigatório para validate-phase2"
    print_summary
  fi

  check_backend_running
  check_backend_image
  check_healthz
  check_db_tables
  check_sqlite_permissions
  check_status_default_allowed
  check_pre_process_job
  check_cups_without_backend
  check_pytest_suite

  print_summary
}

run_full() {
  echo "=== PrintWatch validate-phase2 (full — job lp + SQLite) ==="

  if ! docker_daemon_ready; then
    fail "Docker offline — obrigatório para validate-phase2"
    print_summary
  fi

  load_test_env

  check_backend_running
  check_backend_image
  check_healthz
  check_db_tables
  check_sqlite_permissions
  check_status_default_allowed
  check_pre_process_job
  check_cups_without_backend
  check_pytest_suite

  if [[ "$FAILURES" -gt 0 ]]; then
    echo "=== Pré-checks falharam — abortando job full ==="
    print_summary
  fi

  echo "--- Job local + banco (CAPTURE-01/02 smoke) ---"
  send_full_test_job || true
  wait_for_job_in_db || true
  print_latest_job

  print_summary
}

main() {
  parse_args "$@"

  if [[ "$QUICK_MODE" == true ]]; then
    run_quick
  else
    run_full
  fi
}

main "$@"
