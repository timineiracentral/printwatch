---
phase: 06-costing-chargeback
plan: "01"
subsystem: database
tags: [alembic, sqlalchemy, cups, color_mode, cost_rates]

requires:
  - phase: 05-master-data-organization
    provides: print_jobs schema, org tables
  - phase: 05-2-user-printer-access-policy
    provides: migration chain head c4e8f1a92b03
provides:
  - cost_rates table with valid_from history index
  - print_jobs.color_mode_source column
  - normalize_color_mode() CUPS alias mapping
  - parser integration with captured source hint
  - docs/cups-color-capture.md runbook
affects:
  - 06-02 cost_service and /cost-rates API
  - 06-03 jobs enrichment and PATCH color-mode
  - watcher hot path (parser only, no costing imports)

tech-stack:
  added: []
  patterns:
    - "Canonical color_mode mono|color|NULL at parse time"
    - "cost_rates history via valid_from (no silent overwrite)"
    - "SQLite batch_alter_table for print_jobs columns"

key-files:
  created:
    - backend/alembic/versions/4227505c4a72_cost_rates.py
    - backend/app/services/color_mode.py
    - backend/tests/test_color_mode.py
    - docs/cups-color-capture.md
  modified:
    - backend/app/db/models.py
    - backend/app/services/parser.py
    - backend/tests/test_migrations.py

key-decisions:
  - "Aliases CUPS centralizados em color_mode.py (RESEARCH list)"
  - "color_mode_source=captured apenas quando alias reconhecido"
  - "CostRate com Numeric(12,4) e Decimal no ORM"

patterns-established:
  - "Parser normaliza cor antes de persistir; linhas desconhecidas ficam NULL (pendentes)"
  - "Watcher permanece sem imports de cost_rates/cost_service"

requirements-completed: []

duration: 25min
completed: 2026-05-27
---

# Phase 6 Plan 01: Schema e normalização color_mode Summary

**Migration `cost_rates` + `color_mode_source`, normalizador de aliases CUPS e runbook de captura colorida**

## Performance

- **Duration:** 25 min
- **Started:** 2026-05-27T16:55:00Z
- **Completed:** 2026-05-27T17:20:00Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments

- Tabela `cost_rates` com `rate_mono`, `rate_color`, `valid_from` indexado e timestamps
- Coluna `print_jobs.color_mode_source` (`captured` | `manual` | NULL legado)
- `normalize_color_mode()` mapeia aliases CUPS → `mono` | `color` | pendente
- Parser define `color_mode_source='captured'` quando classificação automática
- Runbook `docs/cups-color-capture.md` para filas CUPS e validação do `page_log`

## Task Commits

1. **Task 1: Migration cost_rates + print_jobs.color_mode_source** - `e8553f3` (feat)
2. **Task 2: Model CostRate + color_mode normalizer** - `e9636e3` (feat)
3. **Task 3: CUPS capture runbook** - `b162275` (docs)

**Plan metadata:** (pending final docs commit)

## Files Created/Modified

- `backend/alembic/versions/4227505c4a72_cost_rates.py` - Migration Alembic encadeada a c4e8f1a92b03
- `backend/app/db/models.py` - Modelo `CostRate` e campo `PrintJob.color_mode_source`
- `backend/app/services/color_mode.py` - Normalização de aliases
- `backend/app/services/parser.py` - Integração captured source
- `backend/tests/test_color_mode.py` - Testes de aliases e parser
- `backend/tests/test_migrations.py` - Head 4227505c4a72 e downgrade cost_rates
- `docs/cups-color-capture.md` - Runbook operacional pt-BR

## Decisions Made

- Aliases mono/color conforme `06-RESEARCH.md` (inclui `mono` canônico na lista mono)
- Valores desconhecidos não descartam a linha — `color_mode` NULL para correção manual posterior
- Watcher inalterado: sem referências a `CostRate` ou `cost_rates`

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- `alembic upgrade head` no host Windows requer `DB_PATH` apontando para arquivo gravável (path `/app/data` do container não existe localmente). Verificado com DB temporário e via `pytest tests/test_migrations.py`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Pronto para **06-02**: `cost_service.py`, CRUD `/cost-rates`, vigência por `valid_from`
- Schema e parser já entregam base para páginas faturáveis (mono/color vs pendente)

## Self-Check: PASSED

- FOUND: backend/alembic/versions/4227505c4a72_cost_rates.py
- FOUND: backend/app/services/color_mode.py
- FOUND: docs/cups-color-capture.md
- FOUND: e8553f3, e9636e3, b162275

---
*Phase: 06-costing-chargeback*
*Completed: 2026-05-27*
