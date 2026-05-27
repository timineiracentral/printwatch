#!/usr/bin/env bash
# PrintWatch — cadastro idempotente de impressora de teste via lpadmin (D-10, D-11)
# Uso: ./scripts/setup-printer.sh
# Requer: container cups running (docker compose up -d --build)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

load_env() {
  if [[ -f "${REPO_ROOT}/.env" ]]; then
    set -a
    # shellcheck source=/dev/null
    source "${REPO_ROOT}/.env"
    set +a
  elif [[ -f "${REPO_ROOT}/.env.example" ]]; then
    echo "[WARN] .env não encontrado — usando .env.example (ajuste valores reais antes de produção)"
    set -a
    # shellcheck source=/dev/null
    source "${REPO_ROOT}/.env.example"
    set +a
  else
    echo "[ERROR] Nem .env nem .env.example encontrados em ${REPO_ROOT}" >&2
    exit 1
  fi
}

is_placeholder_uri() {
  local uri="$1"
  [[ -z "$uri" ]] && return 0
  [[ "$uri" == *"192.0.2."* ]] && return 0
  [[ "$uri" == *"x.x"* ]] && return 0
  return 1
}

resolve_printer_config() {
  PRINTER_NAME="${TEST_PRINTER_NAME:-test_printer}"
  PRINTER_URI="${TEST_PRINTER_URI:-}"
  PRINTER_DRIVER="${TEST_PRINTER_DRIVER:-everywhere}"

  if is_placeholder_uri "$PRINTER_URI"; then
    echo "[INFO] TEST_PRINTER_URI é placeholder — usando fallback cups-pdf para teste sem hardware"
    PRINTER_URI="cups-pdf:/"
    PRINTER_DRIVER="lsb/usr/cups-pdf/CUPS-PDF_noopt.ppd"
  fi

  if [[ "$PRINTER_URI" == socket://* ]] && [[ "$PRINTER_DRIVER" == "everywhere" ]]; then
    echo "[WARN] URI socket:// requer PPD PostScript — defina TEST_PRINTER_DRIVER no .env"
    PRINTER_DRIVER="postscript-hp:0/ps/hpcups.ppd.gz"
  fi
}

ensure_cups_running() {
  cd "${REPO_ROOT}"
  if ! command -v docker >/dev/null 2>&1; then
    echo "[ERROR] Docker não encontrado no PATH" >&2
    exit 1
  fi
  if ! docker info >/dev/null 2>&1; then
    echo "[ERROR] Docker daemon offline — inicie Docker Desktop ou o serviço na VM" >&2
    exit 1
  fi
  if ! docker compose ps --status running 2>/dev/null | grep -qE '(^| )cups( |$)'; then
    echo "[ERROR] Container cups não está running. Execute: docker compose up -d --build" >&2
    exit 1
  fi
}

run_lpadmin_idempotent() {
  docker compose exec -T cups bash -c "
set -euo pipefail
PRINTER_NAME='${PRINTER_NAME}'
PRINTER_URI='${PRINTER_URI}'
PRINTER_DRIVER='${PRINTER_DRIVER}'

if lpstat -p \"\${PRINTER_NAME}\" >/dev/null 2>&1; then
  CURRENT_URI=\$(lpstat -v \"\${PRINTER_NAME}\" 2>/dev/null | awk '{print \$NF}')
  if [ \"\${CURRENT_URI}\" = \"\${PRINTER_URI}\" ]; then
    echo \"Printer \${PRINTER_NAME} already configured (\${PRINTER_URI})\"
  else
    echo \"Updating printer \${PRINTER_NAME}: \${CURRENT_URI} -> \${PRINTER_URI}\"
    lpadmin -p \"\${PRINTER_NAME}\" -v \"\${PRINTER_URI}\" -m \"\${PRINTER_DRIVER}\" -E
  fi
else
  echo \"Creating printer \${PRINTER_NAME} -> \${PRINTER_URI} (driver: \${PRINTER_DRIVER})\"
  lpadmin -p \"\${PRINTER_NAME}\" -v \"\${PRINTER_URI}\" -m \"\${PRINTER_DRIVER}\" -E
fi

cupsaccept \"\${PRINTER_NAME}\"
cupsenable \"\${PRINTER_NAME}\"

# Driverless IPP: evita PPD Samsung que grava print-color-mode=monochrome na fila.
if [[ \"\${PRINTER_URI}\" != cups-pdf:* ]]; then
  if [[ \"\${PRINTER_DRIVER}\" != everywhere ]] && [[ \"\${PRINTER_DRIVER}\" != driverless:* ]]; then
    echo \"[WARN] Driver \${PRINTER_DRIVER} pode forçar P&B — prefira TEST_PRINTER_DRIVER=everywhere\"
  fi
  lpoptions -p \"\${PRINTER_NAME}\" -o print-color-mode=color 2>/dev/null || true
  if grep -q 'Option print-color-mode monochrome' /etc/cups/printers.conf 2>/dev/null; then
    echo \"[WARN] Fila com print-color-mode=monochrome — execute: ./scripts/fix-cups-color-queue.sh \${PRINTER_NAME} \${PRINTER_URI}\"
  fi
fi

lpstat -p \"\${PRINTER_NAME}\"
"
}

main() {
  load_env
  resolve_printer_config
  ensure_cups_running
  run_lpadmin_idempotent
  echo "[OK] Impressora ${PRINTER_NAME} pronta (URI: ${PRINTER_URI})"
  if [[ "${PRINTER_URI}" != cups-pdf:* ]]; then
    echo "[INFO] Padrão de fila: print-color-mode=color (use driver everywhere)"
  fi
}

main "$@"
