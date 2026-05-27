---
phase: 05-master-data-organization
plan: "05"
subsystem: api
tags: [matcher, printer_id, backfill, background-tasks, D-01, D-02, D-03, D-04, INV-04, INV-05]

requires:
  - phase: 05-master-data-organization
    plan: "01"
    provides: print_jobs.printer_id column e índice partial
  - phase: 05-master-data-organization
    plan: "02"
    provides: normalize_printer_name
  - phase: 05-master-data-organization
    plan: "03"
    provides: registry printers + matcher_hooks.schedule_match_for_queue
provides:
  - printer_matcher service (batch 500, on-save, resolve)
  - Loop asyncio 60s no lifespan
  - POST /api/v1/admin/backfill-printer-ids
  - BackgroundTasks em create/update printer
affects:
  - 05-06-import-csv
  - 05-07-settings-ui

tech-stack:
  added: []
  patterns:
    - "Matcher isolado de app.watcher — zero import no capture pipeline"
    - "On-save via BackgroundTasks + batch periódico só printer_id IS NULL"
    - "Backfill admin idempotente até matched_total=0"

key-files:
  created:
    - backend/app/services/printer_matcher.py
    - backend/app/api/v1/admin.py
    - backend/tests/test_matcher.py
    - backend/tests/test_admin_backfill.py
  modified:
    - backend/app/main.py
    - backend/app/api/v1/printers.py
    - backend/app/api/v1/__init__.py

key-decisions:
  - "resolve_printer_id compara via normalize em registry ativo (mesmo padrão printers_service)"
  - "schedule_match_for_queue abre SessionLocal própria para BackgroundTasks"
  - "matcher_hooks mantém lazy import — watcher permanece desacoplado"

patterns-established:
  - "T-05-06: grep vazio em app/watcher para printer_matcher"
  - "T-05-05: match_batch com LIMIT 500 por ciclo"

requirements-completed: [INV-04, INV-05]

duration: 25min
completed: 2026-05-27
---

# Phase 5 Plan 05: Printer Matcher Summary

**Serviço assíncrono de vínculo `printer_id` com batch 60s, on-save via BackgroundTasks e backfill admin idempotente — sem tocar no watcher**

## Performance

- **Duration:** 25 min
- **Started:** 2026-05-27T17:00:00Z
- **Completed:** 2026-05-27T17:25:00Z
- **Tasks:** 2/2 completed
- **Files modified:** 7

## Accomplishments

- `printer_matcher.py` com `resolve_printer_id`, `match_batch`, `match_jobs_for_queue`, `schedule_match_for_queue`
- Lifespan inicia task asyncio (60s) cancelável no shutdown; logs de batch vinculado
- `POST /api/v1/admin/backfill-printer-ids` retorna `{matched_total, remaining_null}`
- Create/update printer usam `BackgroundTasks.add_task(schedule_match_for_queue, ...)`
- 5 testes novos (matcher + backfill + OpenAPI)

## Task Commits

Each task was committed atomically:

1. **Task 1: printer_matcher service** - `3abe487` (feat)
2. **Task 2: Lifespan asyncio loop + admin backfill** - `d392489` (feat)

**Plan metadata:** pending final docs commit

## Files Created/Modified

- `backend/app/services/printer_matcher.py` - Resolve, batch, on-save, count remaining null
- `backend/app/api/v1/admin.py` - Backfill endpoint
- `backend/app/main.py` - `_matcher_loop` no lifespan
- `backend/app/api/v1/printers.py` - BackgroundTasks no create/update
- `backend/app/api/v1/__init__.py` - Router `/admin`
- `backend/tests/test_matcher.py` - 2 órfãos + 1 printer, idempotência batch
- `backend/tests/test_admin_backfill.py` - Backfill e OpenAPI path

## Decisions Made

- Lookup de impressora ativa via normalize (consistente com unicidade do registry)
- `matcher_hooks` continua como façade lazy; implementação real em `printer_matcher`
- Watcher não importa matcher (D-01 preservado)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None

## Next Phase Readiness

- Plan 05-06 (import CSV) pode usar matcher/backfill após import em lote
- Plan 05-07 Settings UI pode expor botão de backfill (opcional)

## Self-Check: PASSED

- FOUND: backend/app/services/printer_matcher.py
- FOUND: backend/app/api/v1/admin.py
- FOUND: backend/tests/test_matcher.py
- FOUND: commit 3abe487
- FOUND: commit d392489

---
*Phase: 05-master-data-organization*
*Completed: 2026-05-27*
