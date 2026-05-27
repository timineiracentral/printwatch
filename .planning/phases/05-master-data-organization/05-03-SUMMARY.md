---
phase: 05-master-data-organization
plan: "03"
subsystem: api
tags: [printers, crud, registry, unmapped-queues, soft-delete, D-11, D-12, D-14, D-18]

requires:
  - phase: 05-master-data-organization
    plan: "01"
    provides: Schema printers, Alembic, print_jobs.printer_id
  - phase: 05-master-data-organization
    plan: "02"
    provides: normalize_printer_name em app.core.normalize
provides:
  - CRUD /api/v1/printers com registry canônico
  - GET /api/v1/printers/unmapped-queues
  - printers_service com unicidade normalizada e soft-delete
  - matcher_hooks.schedule_match_for_queue (lazy até 05-05)
affects:
  - 05-04-crud-org
  - 05-05-matcher
  - 05-07-settings-ui

tech-stack:
  added: []
  patterns:
    - "Registry substitui DISTINCT legado em GET /printers"
    - "Unicidade cups_queue_name via normalize_printer_name na comparação"
    - "Rota /unmapped-queues registrada antes de /{printer_id}"

key-files:
  created:
    - backend/app/schemas/printer.py
    - backend/app/services/printers_service.py
    - backend/app/services/matcher_hooks.py
    - backend/tests/test_printers_api.py
  modified:
    - backend/app/api/v1/printers.py

key-decisions:
  - "active_only=true por default em list; include_inactive via query param"
  - "unmapped-queues retorna nomes normalizados DISTINCT sem match no registry"
  - "schedule_match_for_queue no-op até printer_matcher existir (05-05)"

patterns-established:
  - "Mass assignment bloqueado por schemas Pydantic explícitos (T-05-03)"
  - "SQLAlchemy parametrizado em unmapped-queues (T-05-04)"

requirements-completed: [INV-01, INV-02, INV-03, INV-06, SERVER-04]

duration: 20min
completed: 2026-05-27
---

# Phase 5 Plan 03: Printer Registry API Summary

**CRUD `/api/v1/printers` com registry canônico, soft-delete, unicidade normalizada de `cups_queue_name` e endpoint `unmapped-queues` para onboarding**

## Performance

- **Duration:** 20 min
- **Started:** 2026-05-27T15:05:00Z
- **Completed:** 2026-05-27T15:25:00Z
- **Tasks:** 2/2 completed
- **Files modified:** 6

## Accomplishments

- `PrinterCreate` / `PrinterUpdate` / `PrinterRead` com campos explícitos (sem mass assignment)
- `printers_service` com list, get, create, update, soft_delete e `list_unmapped_queues`
- Rotas CRUD + `GET /unmapped-queues`; hook `schedule_match_for_queue` lazy para matcher (05-05)
- 7 testes em `test_printers_api.py`; suite completa 91 passed

## Task Commits

Each task was committed atomically:

1. **Task 1: Schemas e service layer printers** - `71018ee` (feat)
2. **Task 2: Rotas CRUD + unmapped-queues** - `dcfe6e6` (feat)

**Plan metadata:** pending (docs commit)

## Files Created/Modified

- `backend/app/schemas/printer.py` - Schemas Pydantic do registry
- `backend/app/services/printers_service.py` - CRUD, normalize, 409 duplicado, unmapped
- `backend/app/services/matcher_hooks.py` - Lazy import matcher on-save
- `backend/app/api/v1/printers.py` - Endpoints registry substituindo DISTINCT legado
- `backend/tests/test_printers_api.py` - CRUD, 409, unmapped, OpenAPI, D-21

## Decisions Made

- Lista padrão só impressoras ativas; `active_only=false` inclui soft-deleted
- `unmapped-queues` devolve filas normalizadas sem cadastro (não strings raw com aspas)
- Matcher hook é no-op até `printer_matcher` existir no plan 05-05

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None

## Next Phase Readiness

- Plan 05-04 (CRUD org) pode seguir em paralelo na wave 2
- Plan 05-05 deve implementar `printer_matcher.schedule_match_for_queue` e wire BackgroundTasks

## Self-Check: PASSED

- FOUND: backend/app/schemas/printer.py
- FOUND: backend/app/services/printers_service.py
- FOUND: backend/app/api/v1/printers.py
- FOUND: backend/tests/test_printers_api.py
- FOUND: commit 71018ee
- FOUND: commit dcfe6e6

---
*Phase: 05-master-data-organization*
*Completed: 2026-05-27*
