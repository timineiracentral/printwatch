---
phase: 05-master-data-organization
plan: "02"
subsystem: api
tags: [normalize, core, printer, org-code, D-05, D-16]

requires:
  - phase: 05-master-data-organization
    plan: "01"
    provides: Schema foundation, Alembic, master tables
provides:
  - app.core.normalize module (watcher-safe, no SQLAlchemy)
  - normalize_printer_name centralized with services re-export
  - normalize_org_code for dept/CC UPPERCASE codes
affects:
  - 05-03-crud-printers
  - 05-04-crud-org
  - 05-05-matcher
  - 05-06-import

tech-stack:
  added: []
  patterns:
    - "Normalization in app.core.normalize — importable by watcher without ORM"
    - "services.normalization re-exports for backward compatibility"

key-files:
  created:
    - backend/app/core/normalize.py
  modified:
    - backend/app/services/normalization.py
    - backend/app/services/parser.py
    - backend/scripts/backfill_printer_quotes.py
    - backend/tests/test_normalization.py

key-decisions:
  - "normalize_printer_name e normalize_org_code vivem em app.core.normalize (D-05, D-30)"
  - "services.normalization mantém reexport para testes e código legado"

patterns-established:
  - "Parser, backfill e matcher futuro importam de app.core.normalize diretamente"
  - "normalize_org_code: strip + upper + None se vazio (D-16)"

requirements-completed: [INV-05, DATA-04]

duration: 15min
completed: 2026-05-27
---

# Phase 5 Plan 02: Normalize Core Summary

**Shared normalization in `app.core.normalize` — printer name idempotent strip and org code UPPERCASE — decoupled from SQLAlchemy for watcher-safe imports**

## Performance

- **Duration:** 15 min
- **Started:** 2026-05-27T15:10:00Z
- **Completed:** 2026-05-27T15:25:00Z
- **Tasks:** 2/2 completed
- **Files modified:** 6

## Accomplishments

- `app.core.normalize` criado com `normalize_printer_name` (lógica idêntica à Fase 3)
- `services.normalization` reexporta para compat; `parser` e `backfill` importam do core
- `normalize_org_code` adicionado para códigos dept/CC (strip, upper, None se vazio)
- 14 testes em `test_normalization.py` passando; watcher sem import de `services.normalization`

## Task Commits

Each task was committed atomically:

1. **Task 1: Criar app.core.normalize e migrar implementação** - `3edebc2` (feat)
2. **Task 2: Adicionar normalize_org_code para dept/CC** - `ee3dc6a` (feat)

**Plan metadata:** pending (docs commit)

## Files Created/Modified

- `backend/app/core/normalize.py` - normalize_printer_name + normalize_org_code
- `backend/app/services/normalization.py` - Reexport de compat
- `backend/app/services/parser.py` - Import direto do core
- `backend/scripts/backfill_printer_quotes.py` - Import direto do core
- `backend/tests/test_normalization.py` - Import core + testes org_code

## Decisions Made

- Core module sem dependência ORM — atende D-30 (watcher pode importar no futuro)
- Testes importam `app.core.normalize` diretamente (fonte canônica)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None

## Next Phase Readiness

- Matcher (05-05), CRUD org (05-04) e import CSV (05-06) podem usar `normalize_org_code` e `normalize_printer_name` do mesmo módulo
- Wave 2: 05-03 CRUD printers pronto para iniciar

## Self-Check: PASSED

- FOUND: backend/app/core/normalize.py
- FOUND: commit 3edebc2
- FOUND: commit ee3dc6a

---
*Phase: 05-master-data-organization*
*Completed: 2026-05-27*
