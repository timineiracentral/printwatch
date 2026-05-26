#!/usr/bin/env bash
# PrintWatch — bootstrap idempotente na VM Ubuntu 22.04 (Plan 01-05)
# Uso: ./scripts/bootstrap-vm.sh [--skip-docker-install] [--dry-run]
# Requer: clone do repo, .env configurado (senha != changeme), sudo para apt se Docker ausente

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
TARGET_IP="VM_HOST"
CUPS_WAIT_TIMEOUT=120
SKIP_DOCKER_INSTALL=false
DRY_RUN=false

pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1" >&2; exit 1; }
warn() { echo "[WARN] $1"; }
info() { echo "[INFO] $1"; }

usage() {
  echo "Uso: $0 [--skip-docker-install] [--dry-run]"
  echo "  --skip-docker-install  Não tenta apt install (Docker já presente)"
  echo "  --dry-run              Apenas exibe ações, sem mutação"
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --skip-docker-install) SKIP_DOCKER_INSTALL=true ;;
      --dry-run) DRY_RUN=true ;;
      -h|--help) usage; exit 0 ;;
      *) fail "Argumento desconhecido: $1 (use --help)" ;;
    esac
    shift
  done
}

run_cmd() {
  if [[ "$DRY_RUN" == true ]]; then
    echo "[DRY-RUN] $*"
    return 0
  fi
  "$@"
}

check_ubuntu() {
  if [[ ! -f /etc/os-release ]]; then
    fail "Não foi possível ler /etc/os-release"
  fi
  # shellcheck source=/dev/null
  source /etc/os-release
  if [[ "${ID:-}" != "ubuntu" ]] || [[ ! "${VERSION_ID:-}" =~ ^22\.04 ]]; then
    warn "SO esperado Ubuntu 22.04 — detectado: ${PRETTY_NAME:-desconhecido}"
  else
    pass "Ubuntu 22.04 detectado (${VERSION_ID})"
  fi
}

check_ip_hint() {
  local current_ip=""
  current_ip="$(hostname -I 2>/dev/null | awk '{print $1}' || true)"
  if [[ -n "$current_ip" && "$current_ip" != "$TARGET_IP" ]]; then
    warn "IP atual (${current_ip}) difere do alvo ${TARGET_IP} — confira netplan se necessário"
  elif [[ "$current_ip" == "$TARGET_IP" ]]; then
    pass "IP ${TARGET_IP} confirmado em hostname -I"
  else
    warn "Não foi possível confirmar IP ${TARGET_IP} — prossiga se netplan já foi aplicado"
  fi
}

docker_compose_ready() {
  command -v docker >/dev/null 2>&1 \
    && docker info >/dev/null 2>&1 \
    && docker compose version >/dev/null 2>&1
}

ensure_docker_group() {
  if id -nG "$USER" 2>/dev/null | grep -qw docker; then
    pass "Usuário ${USER} já está no grupo docker"
    return 0
  fi
  if [[ "$DRY_RUN" == true ]]; then
    echo "[DRY-RUN] sudo usermod -aG docker ${USER}"
    warn "Após instalação real: faça re-login ou execute 'newgrp docker'"
    return 0
  fi
  if sudo usermod -aG docker "$USER" 2>/dev/null; then
    warn "Usuário ${USER} adicionado ao grupo docker — re-login ou: newgrp docker"
  else
    warn "Não foi possível adicionar ${USER} ao grupo docker — use sudo para docker compose"
  fi
}

install_docker_if_needed() {
  if docker_compose_ready; then
    pass "Docker e Docker Compose já operacionais ($(docker compose version 2>/dev/null | head -1))"
    ensure_docker_group
    return 0
  fi

  if [[ "$SKIP_DOCKER_INSTALL" == true ]]; then
    fail "Docker/Compose indisponível e --skip-docker-install foi passado"
  fi

  info "Instalando docker.io + docker-compose-plugin via apt..."
  if [[ "$DRY_RUN" == true ]]; then
    echo "[DRY-RUN] sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin"
    return 0
  fi

  sudo apt-get update -qq
  if sudo apt-get install -y docker.io docker-compose-plugin 2>&1; then
    pass "Pacotes docker.io e docker-compose-plugin instalados"
  else
    warn "apt install docker.io falhou (conflito containerd com Docker CE existente é comum)"
    warn "Mantendo instalação Docker CE existente — não force apt docker.io sobre containerd.io"
    if docker_compose_ready; then
      pass "Docker CE pré-instalado continua funcional após falha do apt"
    else
      fail "Docker não responde após tentativa de instalação — instale Docker CE manualmente (docs/vm-deploy-runbook.md)"
    fi
  fi

  ensure_docker_group
  if ! docker_compose_ready; then
    fail "docker compose ainda indisponível — verifique daemon e plugin compose"
  fi
  pass "Docker Compose pronto: $(docker compose version 2>/dev/null | head -1)"
}

ensure_env_file() {
  cd "${REPO_ROOT}"
  if [[ ! -f .env ]]; then
    if [[ ! -f .env.example ]]; then
      fail ".env e .env.example ausentes em ${REPO_ROOT}"
    fi
    info ".env ausente — copiando de .env.example"
    run_cmd cp .env.example .env
    fail "Arquivo .env criado a partir de .env.example — edite CUPS_ADMIN_PASSWORD (remova changeme) e TEST_PRINTER_* antes de continuar"
  fi

  local password
  password="$(grep -E '^CUPS_ADMIN_PASSWORD=' .env | head -1 | cut -d= -f2- | tr -d '\r' || true)"
  if [[ -z "$password" || "$password" == "changeme" ]]; then
    fail "CUPS_ADMIN_PASSWORD ainda é 'changeme' ou vazio em .env — edite credenciais antes do deploy"
  fi
  pass ".env presente com senha CUPS definida (não é changeme)"
}

deploy_compose() {
  cd "${REPO_ROOT}"
  info "Subindo stack CUPS: docker compose up -d --build"
  run_cmd docker compose up -d --build
  pass "docker compose up -d --build concluído"
}

wait_for_cups() {
  cd "${REPO_ROOT}"
  local elapsed=0
  info "Aguardando CUPS HTTP em 127.0.0.1:631 (timeout ${CUPS_WAIT_TIMEOUT}s)..."
  while [[ "$elapsed" -lt "$CUPS_WAIT_TIMEOUT" ]]; do
    if [[ "$DRY_RUN" == true ]]; then
      pass "[DRY-RUN] CUPS healthcheck simulado"
      return 0
    fi
    if docker compose exec -T cups curl -sf http://127.0.0.1:631/ >/dev/null 2>&1; then
      pass "CUPS responde em http://127.0.0.1:631/ (${elapsed}s)"
      return 0
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
  fail "Timeout aguardando CUPS (${CUPS_WAIT_TIMEOUT}s) — verifique: docker compose logs cups"
}

run_setup_printer() {
  cd "${REPO_ROOT}"
  info "Cadastrando impressora: ./scripts/setup-printer.sh"
  if [[ "$DRY_RUN" == true ]]; then
    echo "[DRY-RUN] ./scripts/setup-printer.sh"
    return 0
  fi
  bash "${SCRIPT_DIR}/setup-printer.sh"
  pass "setup-printer.sh concluído"
}

run_validate_quick() {
  cd "${REPO_ROOT}"
  info "Smoke test: bash scripts/validate-phase1.sh --quick"
  if [[ "$DRY_RUN" == true ]]; then
    echo "[DRY-RUN] bash scripts/validate-phase1.sh --quick"
    return 0
  fi
  bash "${SCRIPT_DIR}/validate-phase1.sh" --quick
  pass "validate-phase1.sh --quick exit 0"
}

main() {
  parse_args "$@"
  echo "=== PrintWatch bootstrap-vm ==="
  check_ubuntu
  check_ip_hint
  install_docker_if_needed
  ensure_env_file
  deploy_compose
  wait_for_cups
  run_setup_printer
  run_validate_quick
  echo "=== Bootstrap concluído — execute ./scripts/verify-vm-network.sh para checks de rede ==="
}

main "$@"
