#!/usr/bin/env bash
set -euo pipefail
cd ~/printwatch
chmod +x scripts/fix-cups-color-queue.sh

QUEUE=colorida_corredor
URI=ipp://10.35.0.38:631/ipp/print

echo "=== lpadmin test ==="
docker compose exec -T cups lpadmin -p "$QUEUE" -v "$URI" \
  -m 'openprinting-ppds:0/ppd/openprinting/Samsung/PS/Samsung_X4300_Series.ppd' -E 2>&1 || true

docker compose exec -T cups ls -la /etc/cups/printers.conf 2>&1 || echo "no printers.conf yet"

echo "=== run fix script ==="
bash scripts/fix-cups-color-queue.sh "$QUEUE" "$URI"

echo "=== lpstat ==="
docker compose exec -T cups lpstat -p 2>&1 || true
