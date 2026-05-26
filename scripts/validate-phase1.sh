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

run_quick() {
  echo "=== PrintWatch validate-phase1 (Wave 0 --quick) ==="

  check_file_exists "docker-compose.yml" "required"
  check_file_exists ".env.example" "required"
  check_file_exists "cups/Dockerfile" "optional"
  check_file_exists "scripts/setup-printer.sh" "optional"

  check_env_example_keys
  check_allowed_network
  check_compose_single_service

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
