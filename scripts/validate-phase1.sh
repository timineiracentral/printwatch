#!/usr/bin/env bash
# PrintWatch — validação Fase 1
# Uso: bash scripts/validate-phase1.sh [--quick]
# --quick: smoke tests Wave 0 (<30s, não exige job local)
# (sem flag): suite completa com job local + page_log (Plan 04)

set -euo pipefail

# Git Bash/MSYS: evita conversão de /etc/... para path Windows em `docker compose exec`
if [[ -n "${MSYSTEM:-}" ]] || [[ "$(uname -s 2>/dev/null)" == MINGW* ]]; then
  export MSYS_NO_PATHCONV=1
fi

QUICK_MODE=false
STRICT_RUNTIME=false
FAILURES=0
WARNINGS=0

# SPEC §3.2 — PAGE_LOG_REGEX
PAGE_LOG_REGEX='^(\S+)\s+(\S+)\s+(\d+)\s+\[(.+?)\]\s+total\s+(\d+)\s+(\S+)\s+(\S+)\s+(.+?)\s+(\S+)\s+(\S+)$'

TEST_PRINTER_NAME="${TEST_PRINTER_NAME:-}"

pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; FAILURES=$((FAILURES + 1)); }
warn() { echo "[WARN] $1"; WARNINGS=$((WARNINGS + 1)); }

usage() {
  echo "Uso: $0 [--quick]"
  echo "  --quick   Smoke tests Wave 0 (não envia job local)"
  echo "  (sem flag) Suite completa: quick checks + job lp + page_log (D-13.1)"
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

check_file_exists() {
  local path="$1"
  local required="$2"
  if [[ -f "$path" ]]; then
    pass "Arquivo presente: $path"
  elif [[ "$required" == "required" ]]; then
    fail "Arquivo ausente (obrigatório): $path"
  else
    warn "Arquivo ausente (esperado em plano futuro): $path"
  fi
}

check_env_example_keys() {
  local keys=(
    ALLOWED_NETWORK
    CUPS_ADMIN_USER
    CUPS_ADMIN_PASSWORD
    TEST_PRINTER_NAME
    TEST_PRINTER_URI
    TEST_PRINTER_DRIVER
  )
  local key
  for key in "${keys[@]}"; do
    if grep -qE "^${key}=" .env.example; then
      pass ".env.example contém ${key}"
    else
      fail ".env.example sem chave obrigatória: ${key}"
    fi
  done
}

check_allowed_network() {
  if grep -qE '^ALLOWED_NETWORK=ALLOWED_NETWORK_RANGE' .env.example; then
    pass "ALLOWED_NETWORK=REDACTED_IP/16 em .env.example (D-08)"
  else
    fail "ALLOWED_NETWORK deve ser REDACTED_IP/16 em .env.example (D-08)"
  fi
}

check_compose_single_service() {
  local services
  services="$(
    awk '
      /^services:/ { in_services=1; next }
      in_services && /^  [a-z_]+:/ { print; next }
      in_services && /^[^[:space:]#]/ { in_services=0 }
    ' docker-compose.yml
  )"
  local count
  count="$(printf '%s\n' "$services" | grep -c . || true)"

  if [[ "$count" -eq 1 ]] && echo "$services" | grep -qE '^  cups:'; then
    pass "docker-compose.yml contém apenas serviço cups ativo"
  else
    fail "docker-compose.yml deve ter somente serviço cups ativo (encontrado: ${count})"
    printf '%s\n' "$services" | sed 's/^/  /'
  fi
}

docker_daemon_ready() {
  command -v docker >/dev/null 2>&1 || return 1
  docker info >/dev/null 2>&1
}

cups_container_running() {
  docker compose ps --status running 2>/dev/null | grep -qE '(^| )cups( |$)'
}

check_cups_runtime() {
  if ! docker_daemon_ready; then
    if [[ "$STRICT_RUNTIME" == true ]]; then
      fail "Docker offline — obrigatório para suite completa"
    else
      warn "Docker offline — pulando checks de container (cupsd -t, :631, ACL)"
    fi
    return
  fi

  if ! cups_container_running; then
    if [[ "$STRICT_RUNTIME" == true ]]; then
      fail "Container cups não está running — obrigatório para suite completa"
    else
      warn "Container cups não está running — pulando checks de container"
    fi
    return
  fi

  if docker compose exec -T cups cupsd -t >/dev/null 2>&1; then
    pass "cupsd -t válido no container"
  else
    fail "cupsd -t falhou no container"
  fi

  if docker compose exec -T cups grep -q 'PageLogFormat' /etc/cups/cupsd.conf 2>/dev/null; then
    pass "PageLogFormat ativo em /etc/cups/cupsd.conf"
  else
    fail "PageLogFormat ausente ou vazio em cupsd.conf"
  fi

  local http_code
  http_code="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:631/ 2>/dev/null || true)"
  http_code="${http_code//$'\r'/}"
  if [[ -z "$http_code" ]]; then
    http_code="000"
  fi
  if [[ "$http_code" == "200" ]]; then
    pass "CUPS responde HTTP 200 em :631"
  else
    fail "CUPS não responde HTTP 200 em :631 (código: ${http_code})"
  fi

  if docker compose exec -T cups grep -q 'Allow from REDACTED_IP/16' /etc/cups/cupsd.conf 2>/dev/null; then
    pass "ACL Allow from REDACTED_IP/16 presente em cupsd.conf"
  else
    fail "ACL REDACTED_IP/16 ausente em cupsd.conf"
  fi

  if docker compose exec -T cups grep -q '192.168.0.0/16' /etc/cups/cupsd.conf 2>/dev/null; then
    fail "cupsd.conf contém range RFC1918 genérico 192.168.0.0/16 (D-06)"
  else
    pass "cupsd.conf sem range 192.168.0.0/16 (D-06)"
  fi
}

# Normaliza linha do page_log (cups-pdf pode envolver a linha em aspas)
normalize_page_log_line() {
  local line="$1"
  line="${line//$'\r'/}"
  line="${line#\"}"
  line="${line%\"}"
  printf '%s' "$line"
}

# Valida linha contra PAGE_LOG_REGEX (SPEC §3.2) via Python — bash =~ não suporta \S
PYTHON_BIN=""
resolve_python() {
  if [[ -n "$PYTHON_BIN" ]]; then
    return 0
  fi
  local candidate
  # Windows Git Bash: alias python3 pode apontar para stub da Microsoft Store
  for candidate in python python3; do
    if command -v "$candidate" >/dev/null 2>&1 \
      && "$candidate" -c 'import sys; sys.exit(0)' >/dev/null 2>&1; then
      PYTHON_BIN="$candidate"
      return 0
    fi
  done
  return 1
}

page_log_regex_match() {
  local line="$1"
  if ! resolve_python; then
    echo "python3/python não encontrado para validar PAGE_LOG_REGEX" >&2
    return 1
  fi
  "$PYTHON_BIN" - "$line" "$PAGE_LOG_REGEX" <<'PY'
import re, sys
line = sys.argv[1]
pattern = sys.argv[2]
m = re.match(pattern, line.strip())
if not m:
    sys.exit(1)
# stdout: printer|username|timestamp (pipe-separated)
print("|".join([m.group(1), m.group(2), m.group(4)]))
PY
}

validate_page_log_line() {
  local line="$1"
  local normalized parsed printer username timestamp

  normalized="$(normalize_page_log_line "$line")"

  if ! parsed="$(page_log_regex_match "$normalized" 2>/dev/null)"; then
    fail "page_log linha não corresponde a PAGE_LOG_REGEX (SPEC §3.2)"
    echo "  linha: ${normalized}" >&2
    return 1
  fi

  IFS='|' read -r printer username timestamp <<< "$parsed"

  if [[ "$printer" != "$TEST_PRINTER_NAME" ]]; then
    fail "page_log printer '${printer}' != TEST_PRINTER_NAME '${TEST_PRINTER_NAME}'"
    return 1
  fi
  pass "page_log printer == ${TEST_PRINTER_NAME}"

  if [[ "$username" != *\\* ]]; then
    fail "page_log username sem backslash (esperado DOMINIO\\usuario, D-14): '${username}'"
    return 1
  fi
  pass "page_log username contém backslash: ${username}"

  if [[ -z "$timestamp" ]]; then
    fail "page_log timestamp vazio entre colchetes"
    return 1
  fi
  pass "page_log timestamp parseável: [${timestamp}]"

  return 0
}

test_page_log_regex_unit() {
  local sample="${TEST_PRINTER_NAME} DOMINIO\\usuario 42 [26/May/2026:14:30:00 +0000] total 3 - 192.168.1.10 relatorio.pdf na_iso_a4_210x297mm one-sided"
  if validate_page_log_line "$sample"; then
    pass "PAGE_LOG_REGEX unit test (linha SPEC exemplo)"
  else
    fail "PAGE_LOG_REGEX unit test falhou"
  fi
}

send_local_test_job() {
  pass "Enviando job local lp (D-13.1) para ${TEST_PRINTER_NAME}..."
  if ! docker compose exec -T cups bash -c \
    'echo "PrintWatch phase1 test" | lp -d '"$TEST_PRINTER_NAME"' -U '"'"'DOMINIO\usuario'"'"' -t phase1-local-test' \
    >/dev/null 2>&1; then
    fail "lp job local falhou para impressora ${TEST_PRINTER_NAME}"
    return 1
  fi
  pass "Job local enviado (lp -d ${TEST_PRINTER_NAME})"
  sleep 3
}

validate_local_job_page_log() {
  local last_line

  if ! send_local_test_job; then
    return 1
  fi

  if ! last_line="$(docker compose exec -T cups tail -1 /var/log/cups/page_log 2>/dev/null | tr -d '\r')"; then
    fail "Não foi possível ler /var/log/cups/page_log"
    return 1
  fi

  if [[ -z "$last_line" ]]; then
    fail "page_log vazio após job local"
    return 1
  fi

  pass "page_log contém linha após job local"
  validate_page_log_line "$last_line"
}

run_quick() {
  echo "=== PrintWatch validate-phase1 (--quick) ==="
  STRICT_RUNTIME=false

  check_file_exists "docker-compose.yml" "required"
  check_file_exists ".env.example" "required"
  check_file_exists "cups/Dockerfile" "required"
  check_file_exists "scripts/setup-printer.sh" "required"

  check_env_example_keys
  check_allowed_network
  check_compose_single_service
  check_cups_runtime

  echo "=== Resumo: ${FAILURES} FAIL, ${WARNINGS} WARN ==="
  if [[ "$FAILURES" -gt 0 ]]; then
    exit 1
  fi
  exit 0
}

run_full() {
  echo "=== PrintWatch validate-phase1 (full — job local + page_log) ==="
  STRICT_RUNTIME=true

  check_file_exists "docker-compose.yml" "required"
  check_file_exists ".env.example" "required"
  check_file_exists "cups/Dockerfile" "required"
  check_file_exists "scripts/setup-printer.sh" "required"

  check_env_example_keys
  check_allowed_network
  check_compose_single_service
  load_test_env
  check_cups_runtime

  if [[ "$FAILURES" -gt 0 ]]; then
    echo "=== Pré-checks falharam — abortando job local ==="
    exit 1
  fi

  echo "--- Unit test PAGE_LOG_REGEX ---"
  test_page_log_regex_unit

  echo "--- Job local + page_log (D-13.1, D-14) ---"
  validate_local_job_page_log || true

  echo "=== Resumo: ${FAILURES} FAIL, ${WARNINGS} WARN ==="
  if [[ "$FAILURES" -gt 0 ]]; then
    exit 1
  fi
  exit 0
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
