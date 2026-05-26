---
phase: 02-log-pipeline-data-layer
plan: "05"
subsystem: testing
tags: [nyquist, validation, bash, docker-compose, pytest]

requires:
  - phase: 02-log-pipeline-data-layer
    provides: backend watcher, SQLite, retention, CUPS volume
provides:
  - scripts/validate-phase2.sh — suite Nyquist Fase 2 (--quick + full)
affects:
  - phase-03-backend-api
  - gsd-verify-work

tech-stack:
  added: []
  patterns:
    - "validate-phase2 espelha validate-phase1: pass/fail/warn, --quick, exit code por FAILURES"
    - "healthz via Python urllib (imagem slim sem curl)"
    - "pytest no host em backend/ (tests/ não copiado na imagem Docker)"

key-files:
  created:
    - scripts/validate-phase2.sh
  modified: []

key-decisions:
  - "healthz: urllib no container em vez de curl (ausente na imagem python:3.11-slim)"
  - "pytest: executar em backend/ no host; diretório tests/ não está no Dockerfile de produção"
  - "full job wait: buscar por job_name único (phase2-local-test-<epoch>) em vez de count, por idempotência UNIQUE"

patterns-established:
  - "ensure_test_printer: chama setup-printer.sh se lpstat não encontrar TEST_PRINTER_NAME"

requirements-completed: []

duration: 25min
completed: "2026-05-26T21:55:00.000Z"
checkpoint_status: awaiting_human_verify
---

# Phase 2 Plan 05: Nyquist Validation Summary

**Suite validate-phase2.sh com 11 checks --quick verdes; full local passa job lp → SQLite em ~3s; checkpoint humano Windows/AD pendente.**

## Performance

- **Duration:** ~25 min
- **Tasks:** 1/2 (checkpoint humano pendente)
- **Files modified:** 1

## Accomplishments

- `scripts/validate-phase2.sh` criado com checks QUICK (backend, healthz, tabelas, permissões 600, status default, pre_process_job, CAPTURE-04, pytest) e FULL (lp + ingest SQLite).
- `bash scripts/validate-phase2.sh --quick` — 0 FAIL, ~16s (ambiente local Docker).
- `bash scripts/validate-phase2.sh` (full) — 0 FAIL após `setup-printer.sh` (job `DOMINIO\usuario` no banco em ~3s).

## Task Commits

1. **Task 1: Criar validate-phase2.sh** — `25cf4bd` (feat)

**Checkpoint:** Task 2 (human-verify Windows AD) — aguardando usuário.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] healthz sem curl no container**
- **Found during:** Task 1
- **Issue:** `curl -sf http://localhost:8000/healthz` falha na imagem slim
- **Fix:** `python -c` com `urllib.request`
- **Files modified:** scripts/validate-phase2.sh
- **Commit:** `25cf4bd`

**2. [Rule 3 - Blocking] pytest tests/ ausente na imagem backend**
- **Found during:** Task 1
- **Issue:** Dockerfile copia apenas `app/`, não `tests/`
- **Fix:** pytest executado em `backend/` no host (alinhado a 02-VALIDATION.md)
- **Files modified:** scripts/validate-phase2.sh
- **Commit:** `25cf4bd`

**3. [Rule 1 - Bug] full suite falhava com count/idempotente**
- **Found during:** Task 1 verify
- **Issue:** reexecuções não incrementam count por UNIQUE constraint
- **Fix:** job title único + wait por `job_name`; `ensure_test_printer` antes do lp
- **Commit:** `25cf4bd`

## Self-Check: PASSED

- FOUND: scripts/validate-phase2.sh
- FOUND: commit 25cf4bd

## Próximo passo (humano)

Ver checkpoint em 02-05-PLAN.md Task 2: imprimir de PC Windows com usuário AD, confirmar `DOMINIO\usuario` no banco em ≤30s, responder **aprovado**.
