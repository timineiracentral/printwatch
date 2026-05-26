---
phase: 01-infrastructure-print-server
plan: 04
subsystem: infra
tags: [cups, page_log, ipp, e2e-validation, windows-client, VM_HOST]

requires:
  - phase: 01-05
    provides: "VM CUPS operacional em VM_HOST:631, test_printer cadastrada"
  - phase: 01-03
    provides: "setup-printer.sh, phase1-validation docs base"
provides:
  - "validate-phase1.sh full mode com PAGE_LOG_REGEX e job local lp"
  - "docs/phase1-validation.md procedimento E2E D-13/D-14"
  - "Cadeia compose→CUPS→impressora→page_log validada local + remoto IPP"
  - "Username AD observado: DOMAIN\user.example (formato DOMINIO\\usuario)"
affects: [02-log-pipeline]

tech-stack:
  added: [PAGE_LOG_REGEX gate, phase1-validation runbook]
  patterns:
    - "Job local: lp -U 'DOMINIO\\usuario' + assert regex page_log"
    - "Job remoto: Windows IPP → CUPS page_log; username real AD no log"
    - "Backend físico: TEST_PRINTER_URI deve incluir porta :631"

key-files:
  created:
    - docs/phase1-validation.md
  modified:
    - scripts/validate-phase1.sh
    - docs/vm-setup.md
    - docs/phase1-validation.md

key-decisions:
  - "Username Windows IPP registra como DOMAIN\usuario — válido D-14; normalização Fase 2 se necessário"
  - "TEST_PRINTER_URI backend: ipp://PRINTER_HOST:631/ipp/print (porta 631 explícita obrigatória para impressão física)"
  - "Cliente Windows usa http://VM_HOST:631/printers/test_printer — distinto do URI backend CUPS→impressora"

patterns-established:
  - "Gate Fase 1: validate-phase1.sh full (local) + checkpoint IPP Windows (remoto)"
  - "Operador corrige .env na VM e re-executa lpadmin -v após descobrir URI backend"

requirements-completed: [SERVER-01, SERVER-02, SERVER-03]

duration: 45min
completed: 2026-05-26
---

# Phase 01 Plan 04: E2E Validation Summary

**Suite validate-phase1.sh com regex page_log, guia E2E IPP Windows e checkpoint aprovado — job remoto gera linha DOMAIN\user.example no page_log com impressão física**

## Performance

- **Duration:** 45 min (Tasks 1–2 automatizadas; Task 3 aguardou deploy VM + operador)
- **Started:** 2026-05-26T16:45:00Z
- **Completed:** 2026-05-26T19:30:00Z
- **Tasks:** 3 (2 auto + 1 checkpoint aprovado)
- **Files modified:** 3

## Accomplishments

- `scripts/validate-phase1.sh` modo full: job local `lp`, `PAGE_LOG_REGEX` (SPEC §3.2), asserts printer/username/timestamp
- `docs/phase1-validation.md` documenta D-13 modo 1 (automático) e modo 2 (IPP Windows), checklist D-14 e ACL
- **Checkpoint Task 3 aprovado** — job remoto desde `CLIENT_HOST`, impressão física confirmada, `page_log` com linha recente
- Walking skeleton Fase 1 completo: compose → CUPS → impressora → `page_log`

## Task Commits

Each task was committed atomically:

1. **Task 1: Estender validate-phase1.sh com job local e regex page_log** - `9ca709d` (test)
2. **Task 2: Documentar validação remota IPP e critérios page_log** - `7e1a66b` (docs)
3. **Task 3: Checkpoint — validação remota IPP e aceite page_log** - aprovado operador 2026-05-26 (evidência abaixo; commit docs neste plano)

**Plan metadata:** pendente neste commit (docs)

## Checkpoint Evidence (Task 3 — Approved)

**Data:** 2026-05-26  
**Operador:** job remoto IPP Windows + correção URI backend na VM.

| Item | Resultado |
|------|-----------|
| Cliente Windows | Porta IPP `http://VM_HOST:631/printers/test_printer` (Internet Port) |
| Origem job | `CLIENT_HOST` |
| access_log | `Create-Job` + `Send-Document` → `successful-ok` |
| page_log | `test_printer` **DOMAIN\user.example** from `CLIENT_HOST` — job `"Página de teste"` |
| Impressão física | Confirmada após `lpadmin -v ipp://PRINTER_HOST:631/ipp/print` |
| `.env` VM | `TEST_PRINTER_URI` atualizado com URI correta |

**Username (D-14):** formato `DOMINIO\usuario` observado como `DOMAIN\user.example` — aceito; não bloqueia Fase 1.

**Job local (D-13.1):** `bash scripts/validate-phase1.sh` — coberto por Tasks 1–2 (`9ca709d`).

## Files Created/Modified

- `scripts/validate-phase1.sh` — Modo full: lp job, sleep 3, tail page_log, regex + field asserts
- `docs/phase1-validation.md` — Seções 1–4: local, IPP Windows, page_log, ACL; troubleshooting URI backend (Seção 5)
- `docs/vm-setup.md` — Link para phase1-validation.md no checklist

## Decisions Made

- Username real AD no `page_log` difere do placeholder `DOMINIO\usuario` do job local — documentar para parser Fase 2
- URI backend da impressora física **deve** incluir `:631` (`ipp://PRINTER_HOST:631/ipp/print`); URI sem porta falhou na impressão física
- URL IPP para clientes Windows (`VM_HOST:631`) é independente do `TEST_PRINTER_URI` (CUPS → impressora na rede)

## Deviations from Plan

### Operator Discovery (Checkpoint — não previsto no plano)

**1. URI backend sem porta :631 impediu impressão física**
- **Found during:** Task 3 (checkpoint IPP remoto)
- **Issue:** `TEST_PRINTER_URI` configurado como `ipp://PRINTER_HOST/ipp/print` (sem `:631`) — job chegava ao CUPS e registrava `page_log`, mas a impressora física não imprimia
- **Fix:** Operador atualizou `.env` na VM e re-aplicou `lpadmin -v ipp://PRINTER_HOST:631/ipp/print`; impressão física confirmada
- **Lesson:** Backend CUPS→impressora HP/Samsung IPP exige porta explícita `:631`; cliente Windows continua usando `http://VM_HOST:631/printers/<nome>`
- **Files modified:** `.env` na VM (não versionado); documentado em `docs/phase1-validation.md` Seção 5

---

**Total deviations:** 1 operador (URI backend :631)  
**Impact on plan:** Não altera critérios de aceite — page_log e job remoto já satisfaziam D-13/D-14; correção necessária para entrega física real (SERVER-03 operacional).

## Issues Encountered

- Bloqueio B-01-04-VM (sem deploy) — resolvido pelo plano 01-05 antes do checkpoint
- Impressão física falhou até correção da URI backend — resolvido pelo operador na VM

## Auth Gates

None.

## Threat Flags

Omitido — superfícies conforme threat_model do plano (page_log via docker exec, ACL REDACTED_IP/16).

## Next Phase Readiness

- Fase 1 infra completa — pronta para Fase 2 (Log Pipeline & Data Layer)
- Parser Fase 2 deve aceitar `DOMAIN\usuario` e eventualmente normalizar usernames
- `page_log` volume persistente; watcher lerá `/var/log/cups/page_log`

## Self-Check: PASSED

- FOUND: scripts/validate-phase1.sh (extended)
- FOUND: docs/phase1-validation.md
- FOUND: docs/vm-setup.md (link)
- FOUND: 9ca709d
- FOUND: 7e1a66b

---
*Phase: 01-infrastructure-print-server*
*Plan: 04 — E2E validation*
*Completed: 2026-05-26*
