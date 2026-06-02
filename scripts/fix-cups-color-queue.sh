#!/usr/bin/env bash
# Configura fila CUPS Samsung com impressão colorida (evita print-color-mode=monochrome do PPD).
# Uso: ./scripts/fix-cups-color-queue.sh <queue_name> <ipp_uri>
# Ex.: ./scripts/fix-cups-color-queue.sh colorida_corredor ipp://10.1.0.38:631/ipp/print

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

QUEUE_NAME="${1:?Informe o nome da fila (ex.: colorida_corredor)}"
PRINTER_URI="${2:?Informe a URI IPP (ex.: ipp://HOST:631/ipp/print)}"
PPD="${3:-openprinting-ppds:0/ppd/openprinting/Samsung/PS/Samsung_X4300_Series.ppd}"

cd "${REPO_ROOT}"
if ! docker compose ps --status running 2>/dev/null | grep -qE '(^| )cups( |$)'; then
  echo "[ERROR] Container cups não está running." >&2
  exit 1
fi

echo "[INFO] Configurando fila ${QUEUE_NAME} (Samsung PPD + cor, sem travar fila)..."
docker compose exec -T cups bash -c "
set -euo pipefail
cancel -a '${QUEUE_NAME}' 2>/dev/null || true
lpadmin -x '${QUEUE_NAME}' 2>/dev/null || true
rm -f '/etc/cups/ppd/${QUEUE_NAME}.ppd'
if ! lpadmin -p '${QUEUE_NAME}' -v '${PRINTER_URI}' -m '${PPD}' -E; then
  echo '[WARN] lpadmin com PPD Samsung falhou; tentando driver everybodysuccessful...' >&2
  lpadmin -p '${QUEUE_NAME}' -v '${PRINTER_URI}' -m everywhere -E
fi
lpoptions -p '${QUEUE_NAME}' -o ColorModel=Color
lpadmin -p '${QUEUE_NAME}' -o printer-error-policy=abort-job
if [ -f /etc/cups/printers.conf ]; then
  sed -i '/Option print-color-mode monochrome/d' /etc/cups/printers.conf
  if ! grep -q 'Option print-color-mode color' /etc/cups/printers.conf; then
    sed -i \"/<Printer ${QUEUE_NAME}>/,/<\\/Printer>/ s|</Printer>|Option print-color-mode color\\n</Printer>|\" /etc/cups/printers.conf
  fi
else
  echo '[WARN] /etc/cups/printers.conf ausente após lpadmin; reinicie o container cups se a fila não aparecer.' >&2
fi
kill -HUP 1 2>/dev/null || true
sleep 1
cupsaccept '${QUEUE_NAME}'
cupsenable '${QUEUE_NAME}'
lpstat -p '${QUEUE_NAME}'
grep -A2 'Printer ${QUEUE_NAME}' /etc/cups/printers.conf | grep print-color || true
"

echo "[OK] Fila ${QUEUE_NAME} pronta. Teste: docker compose exec cups lp -d ${QUEUE_NAME} /usr/share/cups/data/default-testpage.pdf"
