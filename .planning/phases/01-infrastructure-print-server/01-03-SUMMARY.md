---
phase: 01-infrastructure-print-server
plan: 03
subsystem: infra
tags: [cups, lpadmin, vm-setup, docker, idempotent-script, wave-3]

requires:
  - phase: 01-02
    provides: "Container CUPS buildável, validate-phase1.sh runtime checks"
provides:
  - "scripts/setup-printer.sh idempotente via docker compose exec lpadmin"
  - "docs/vm-setup.md checklist VM VM_HOST hostname printwatch"
  - "README.md quick start apontando para vm-setup.md"
  - "Impressora test_printer cadastrada (cups-pdf fallback em dev)"
affects: [01-04]

tech-stack:
  added: [lpadmin idempotent shell, cups-pdf virtual queue]
  patterns:
    - "Env load .env → .env.example fallback com WARN"
    - "Placeholder URI auto-fallback cups-pdf:/ + CUPS-PDF_noopt.ppd"
    - "Idempotência: lpstat -p + compara URI antes de lpadmin"

key-files:
  created:
    - scripts/setup-printer.sh
    - docs/vm-setup.md
    - README.md
  modified:
    - scripts/validate-phase1.sh
    - .env.example

key-decisions:
  - "Fallback cups-pdf usa PPD lsb/usr/cups-pdf/CUPS-PDF_noopt.ppd — driver name cups-pdf falha no CUPS 2.4"
  - "setup-printer.sh detecta placeholder 192.0.2.50 e aplica fallback automaticamente"
  - "validate-phase1.sh exige setup-printer.sh como required (PASS) não optional (WARN)"

patterns-established:
  - "Cadastro impressora: host script → docker compose exec -T cups bash -c lpadmin"
  - "Segunda execução setup-printer retorna already configured exit 0"

requirements-completed: [SERVER-03, SERVER-01, DEPLOY-02]

duration: 28min
completed: 2026-05-26
---

# Phase 01 Plan 03: Printer Setup & VM Docs Summary

**Script idempotente setup-printer.sh com fallback cups-pdf, checklist VM VM_HOST/printwatch e README de deploy — fila test_printer enabled no CUPS**

## Performance

- **Duration:** 28 min
- **Started:** 2026-05-26T16:15:00Z
- **Completed:** 2026-05-26T16:43:00Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- `scripts/setup-printer.sh` cadastra/atualiza impressora via `lpadmin` dentro do container com lógica idempotente (lpstat + compara URI)
- `docs/vm-setup.md` documenta hostname printwatch, IP VM_HOST, Docker, deploy e passo manual lpadmin equivalente
- `README.md` com quick start de 4 comandos e link para guia VM
- Impressora `test_printer` cadastrada com fallback `cups-pdf:/` quando URI é placeholder; segunda execução retorna `already configured`

## Task Commits

Each task was committed atomically:

1. **Task 1: Criar scripts/setup-printer.sh idempotente** - `65f7a73` (feat)
2. **Task 2: Documentar preparação da VM em docs/vm-setup.md** - `8f9e452` (docs)
3. **Task 3: Atualizar README e executar cadastro de impressora** - `9007ff4` (feat)

**Plan metadata:** pendente neste commit (docs)

## Files Created/Modified

- `scripts/setup-printer.sh` — Carrega TEST_PRINTER_* do .env, lpadmin idempotente via docker exec
- `docs/vm-setup.md` — Checklist operacional VM Ubuntu 22.04, netplan, manual lpadmin
- `README.md` — Quick start Fase 1, link docs/vm-setup.md
- `scripts/validate-phase1.sh` — setup-printer.sh required (PASS)
- `.env.example` — Nota fallback cups-pdf atualizada

## Decisions Made

- Driver fallback cups-pdf: `lsb/usr/cups-pdf/CUPS-PDF_noopt.ppd` (nome `cups-pdf` falha com cups-driverd no CUPS 2.4)
- Detecção automática de placeholder URI (`192.0.2.50`, `x.x`) aplica fallback sem editar .env em dev
- Documentação manual em vm-setup.md inclui variantes IPP, socket e cups-pdf

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrigido driver fallback cups-pdf**
- **Found during:** Task 3 (execução setup-printer.sh)
- **Issue:** `lpadmin -m cups-pdf` falhou — `cups-driverd failed to get PPD file`
- **Fix:** Usar `-m lsb/usr/cups-pdf/CUPS-PDF_noopt.ppd` com URI `cups-pdf:/`
- **Files modified:** scripts/setup-printer.sh, docs/vm-setup.md, .env.example
- **Verification:** setup-printer.sh exit 0; lpstat -p test_printer enabled
- **Committed in:** 9007ff4 (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1)
**Impact on plan:** Correção necessária para cadastro sem hardware; sem scope creep.

## Issues Encountered

- **Docker Desktop offline inicialmente no Windows:** iniciado manualmente via Start-Process; compose build/up e setup-printer executados com sucesso após daemon online
- **validate-phase1.sh --quick:** 2 FAIL pré-existentes (PageLogFormat/ACL grep no container) — fora do escopo deste plan; checks estáticos e setup-printer PASS

## User Setup Required

Para impressora HP/Samsung real na VM:

```bash
# Editar .env com URI real descoberta via lpinfo -v
TEST_PRINTER_URI=ipp://192.0.2.50/ipp/print
TEST_PRINTER_DRIVER=everywhere
./scripts/setup-printer.sh
```

Sem hardware: deixar placeholder — script usa cups-pdf automaticamente.

## Next Phase Readiness

- Plan 04 pode executar job local `lp` e validar page_log — fila test_printer cadastrada e enabled
- Job remoto IPP (D-13 modo 2) requer impressora real ou cliente na rede REDACTED_LAN
- Validar PageLogFormat/ACL runtime checks na VM se grep falhar no ambiente Windows dev

## Self-Check: PASSED

- FOUND: scripts/setup-printer.sh
- FOUND: docs/vm-setup.md
- FOUND: README.md
- FOUND: 65f7a73, 8f9e452, 9007ff4
- FOUND: docker compose exec cups lpstat -p test_printer (enabled)

---
*Phase: 01-infrastructure-print-server*
*Completed: 2026-05-26*
