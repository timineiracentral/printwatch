#!/usr/bin/env bash
# PrintWatch — validação Wave 0 (Fase 1)
# Uso: bash scripts/validate-phase1.sh [--quick]
# --quick (padrão): smoke tests sem container rodando

set -euo pipefail

QUICK_MODE=true
FAILURES=0
WARNINGS=0

pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; FAILURES=$((FAILURES + 1)); }
warn() { echo "[WARN] $1"; WARNINGS=$((WARNINGS + 1)); }

usage() {
  echo "Uso: $0 [--quick]"
  echo "  --quick   Smoke tests Wave 0 (padrão; não exige container)"
  echo "  (sem flag) Executa suite completa (reservado para Plan 04)"
}

run_full() {
  echo "[INFO] full suite após Plan 04"
  exit 0
}

parse_args() {
  if [[ $# -eq 0 ]]; then
    QUICK_MODE=true
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
    warn "Docker offline — pulando checks de container (cupsd -t, :631, ACL)"
    return
  fi

  if ! cups_container_running; then
    warn "Container cups não está running — pulando checks de container"
    return
  fi

  if docker compose exec -T cups cupsd -t >/dev/null 2>&1; then
    pass "cupsd -t válido no container"
  else
    fail "cupsd -t falhou no container"
  fi

  if docker compose exec -T cups grep -q 'PageLogFormat "%p %u %j %T %P %C' /etc/cups/cupsd.conf 2>/dev/null; then
    pass "PageLogFormat ativo em /etc/cups/cupsd.conf"
  else
    fail "PageLogFormat ausente ou vazio em cupsd.conf"
  fi

  local http_code
  http_code="$(curl -sf -o /dev/null -w '%{http_code}' http://127.0.0.1:631/ 2>/dev/null || echo "000")"
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

run_quick() {
  echo "=== PrintWatch validate-phase1 (Wave 0 --quick) ==="

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

main() {
  parse_args "$@"

  if [[ "$QUICK_MODE" == true ]]; then
    run_quick
  else
    run_full
  fi
}

main "$@"
