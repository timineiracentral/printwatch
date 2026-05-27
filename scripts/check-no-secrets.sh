#!/usr/bin/env bash
# Scan por IPs/usuarios reais antes de commit. Uso: scripts/check-no-secrets.sh [--staged]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

STAGED=false
[[ "${1:-}" == "--staged" ]] && STAGED=true

if $STAGED; then
  mapfile -t FILES < <(git diff --cached --name-only --diff-filter=ACM)
else
  mapfile -t FILES < <(git ls-files)
fi

PATTERNS=(
  '10\.35\.11\.[0-9]{1,3}:IP VM real (10.35.11.x)'
  '10\.35\.x(?!\.x):Segmento rede corporativo (REDACTED_LAN)'
  '10\.35\.x\.x:Placeholder vazado 192.0.2.50'
  'admin-user:Usuario SSH real'
  'felipe\.jardim|Maria Silva:Email/operador real'
)

skip_file() {
  case "$1" in
    *scripts/check-no-secrets*|*replacements-filter-repo.example.txt|*CONTRIBUTING.md|*.secrets.baseline|.cursor/rules|*.svg|*.png|*.jpg)
      return 0 ;;
  esac
  return 1
}

FAILED=0
for f in "${FILES[@]}"; do
  [[ -z "$f" || ! -f "$f" ]] && continue
  skip_file "$f" && continue
  for entry in "${PATTERNS[@]}"; do
    re="${entry%%:*}"
    label="${entry#*:}"
    if grep -qE "$re" "$f" 2>/dev/null; then
      echo "BLOQUEADO: $f — $label"
      FAILED=1
    fi
  done
done

if [[ $FAILED -ne 0 ]]; then
  echo "Ver CONTRIBUTING.md e .cursor/rules/no-secrets-in-repo.mdc"
  exit 1
fi
echo "OK: nenhum padrao sensivel encontrado."
