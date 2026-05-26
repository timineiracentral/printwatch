#!/bin/bash
set -euo pipefail

export ALLOWED_NETWORK="${ALLOWED_NETWORK:-REDACTED_IP/16}"
CUPS_ADMIN_USER="${CUPS_ADMIN_USER:-admin}"
CUPS_ADMIN_PASSWORD="${CUPS_ADMIN_PASSWORD:-changeme}"

# T-01-04: validação básica de CIDR — rejeita injection via env
if [[ -z "${ALLOWED_NETWORK}" ]] || [[ ! "${ALLOWED_NETWORK}" =~ ^[0-9./]+$ ]]; then
  echo "ALLOWED_NETWORK inválido: ${ALLOWED_NETWORK}" >&2
  exit 1
fi

# T-01-05: envsubst whitelist — substituir apenas ALLOWED_NETWORK
envsubst '${ALLOWED_NETWORK}' \
  < /etc/cups/cupsd.conf.template \
  > /etc/cups/cupsd.conf

# D-19: usuário admin CUPS (@SYSTEM / lpadmin)
if ! id "${CUPS_ADMIN_USER}" &>/dev/null; then
  useradd -r -G lpadmin,sys,root "${CUPS_ADMIN_USER}"
  echo "${CUPS_ADMIN_USER}:${CUPS_ADMIN_PASSWORD}" | chpasswd
fi

mkdir -p /var/log/cups /var/spool/cups

/usr/sbin/cupsd -t || exit 1
exec /usr/sbin/cupsd -f
