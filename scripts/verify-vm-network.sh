#!/usr/bin/env bash
# PrintWatch — verificação de rede/firewall CUPS na VM (Plan 01-05)
# Uso: ./scripts/verify-vm-network.sh [--from-ip IP]
# Rodar na VM após bootstrap-vm.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
FROM_IP=""
FAILURES=0
WARNINGS=0

pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; FAILURES=$((FAILURES + 1)); }
warn() { echo "[WARN] $1"; WARNINGS=$((WARNINGS + 1)); }
info() { echo "[INFO] $1"; }

usage() {
  echo "Uso: $0 [--from-ip IP]"
  echo "  --from-ip  Documenta teste remoto; na VM só valida binding local + ACL"
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --from-ip)
        shift
        FROM_IP="${1:-}"
        if [[ -z "$FROM_IP" ]]; then
          echo "[FAIL] --from-ip requer um endereço" >&2
          exit 1
        fi
        ;;
      -h|--help) usage; exit 0 ;;
      *) echo "[FAIL] Argumento desconhecido: $1" >&2; usage; exit 1 ;;
    esac
    shift
  done
}

cd "${REPO_ROOT}"

check_container_running() {
  if ! command -v docker >/dev/null 2>&1; then
    fail "Docker não encontrado no PATH"
    return
  fi
  if ! docker info >/dev/null 2>&1; then
    fail "Docker daemon offline"
    return
  fi
  if docker compose ps --status running 2>/dev/null | grep -qE '(^| )cups( |$)'; then
    pass "Container cups running"
  else
    fail "Container cups não está running — execute: docker compose up -d --build"
  fi
}

check_cups_http_local() {
  local http_code
  http_code="$(curl -sf -o /dev/null -w '%{http_code}' http://127.0.0.1:631/ 2>/dev/null || echo "000")"
  http_code="${http_code//$'\r'/}"
  if [[ "$http_code" == "200" ]]; then
    pass "curl http://127.0.0.1:631/ → HTTP 200"
  else
    fail "curl http://127.0.0.1:631/ → HTTP ${http_code} (esperado 200)"
  fi
}

check_port_published() {
  if command -v ss >/dev/null 2>&1 && ss -tlnp 2>/dev/null | grep -q ':631'; then
    pass "Porta 631 em escuta no host (ss -tlnp)"
    return
  fi
  local mapping
  mapping="$(docker compose port cups 631 2>/dev/null || true)"
  if [[ -n "$mapping" ]]; then
    pass "Porta 631 publicada via compose: ${mapping}"
  else
    fail "Porta 631 não encontrada (ss nem docker compose port)"
  fi
}

check_acl_cupsd() {
  if ! docker compose ps --status running 2>/dev/null | grep -qE '(^| )cups( |$)'; then
    fail "ACL: container cups offline"
    return
  fi
  if docker compose exec -T cups grep -q 'Allow from REDACTED_IP/16' /etc/cups/cupsd.conf 2>/dev/null; then
    pass "ACL Allow from REDACTED_IP/16 em /etc/cups/cupsd.conf"
  else
    fail "ACL REDACTED_IP/16 ausente em cupsd.conf"
  fi
  if docker compose exec -T cups grep 'Allow from' /etc/cups/cupsd.conf 2>/dev/null | head -5; then
    info "Trecho Allow from (primeiras linhas):"
    docker compose exec -T cups grep 'Allow from' /etc/cups/cupsd.conf 2>/dev/null | head -5 | sed 's/^/  /' || true
  fi
}

check_ufw_optional() {
  if ! command -v ufw >/dev/null 2>&1; then
    info "ufw não instalado — firewall pode ser externo (XCP-ng/rede)"
    return
  fi
  local ufw_status
  ufw_status="$(sudo ufw status 2>/dev/null || ufw status 2>/dev/null || true)"
  if echo "$ufw_status" | grep -qi inactive; then
    pass "ufw inativo — sem bloqueio local em 631"
    return
  fi
  if echo "$ufw_status" | grep -qE '631/tcp'; then
    pass "ufw ativo com regra 631/tcp"
  else
    warn "ufw ativo sem regra explícita 631/tcp — firewall corporativo pode bloquear LAN; teste curl de outro host REDACTED_LAN"
  fi
}

hint_remote_from_ip() {
  if [[ -n "$FROM_IP" ]]; then
    info "Teste remoto sugerido (executar em ${FROM_IP}, não na VM):"
    echo "  curl -I http://VM_HOST:631/"
  else
    info "Teste remoto (outro host REDACTED_LAN): curl -I http://VM_HOST:631/ → HTTP 200"
  fi
}

main() {
  parse_args "$@"
  echo "=== PrintWatch verify-vm-network ==="
  check_container_running
  check_cups_http_local
  check_port_published
  check_acl_cupsd
  check_ufw_optional
  hint_remote_from_ip
  echo "=== Resumo: ${FAILURES} FAIL, ${WARNINGS} WARN ==="
  if [[ "$FAILURES" -gt 0 ]]; then
    exit 1
  fi
  exit 0
}

main "$@"
