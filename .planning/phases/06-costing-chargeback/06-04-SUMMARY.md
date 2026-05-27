---
phase: 06-costing-chargeback
plan: "04"
subsystem: api
tags: [chargeback, csv, export, fastapi, costing]

requires:
  - phase: 06-costing-chargeback
    plan: "02"
    provides: aggregate_cost_by_dimension, buckets, outside_policy exclusion
provides:
  - chargeback_export service with iter_chargeback_csv and count_chargeback_groups
  - GET /export/chargeback/by-cost-center and /by-department
affects:
  - 06-05 Settings Tarifas + UI custo Jobs

tech-stack:
  added: []
  patterns:
    - "Chargeback CSV reuses aggregate_cost_by_dimension; default date range = current calendar month"
    - "StreamingResponse UTF-8 BOM + semicolon delimiter aligned with csv_export"

key-files:
  created:
    - backend/app/services/chargeback_export.py
    - backend/tests/test_chargeback_export.py
  modified:
    - backend/app/api/v1/export.py

key-decisions:
  - "date_from/date_to opcionais: default mês calendário SP via _month_bounds_local"
  - "Páginas pendentes exibidas na coluna Páginas mono no bucket homônimo"
  - "Cap 100k aplica-se a grupos+buckets, não linhas de job"

patterns-established:
  - "Filenames chargeback_cc_YYYYMMDD.csv e chargeback_dept_YYYYMMDD.csv"
  - "Sem campos de fatura/contabilidade no CSV (CHRG-04)"

requirements-completed: [CHRG-01, CHRG-02, CHRG-03, CHRG-04, COST-04]

duration: 25min
completed: 2026-05-27
---

# Phase 6 Plan 04: Chargeback CSV Exports Summary

**Exports CSV internos de chargeback por centro de custo e departamento com buckets D-17 e exclusão outside_policy**

## Performance

- **Duration:** 25 min
- **Started:** 2026-05-27T22:00:00Z
- **Completed:** 2026-05-27T22:25:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- `chargeback_export.py` com `iter_chargeback_csv`, `count_chargeback_groups`, resolução de datas
- Cabeçalho pt-BR: Grupo; Páginas mono; Páginas color; Custo estimado (R$)
- Rotas `GET /api/v1/export/chargeback/by-cost-center` e `/by-department`
- Testes: outside_policy excluído, buckets usuário/impressora não cadastrados, BOM UTF-8

## Task Commits

1. **Task 1: chargeback_export service** - `ef2fc43` (feat)
2. **Task 2: Rotas export chargeback** - `cce4296` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `backend/app/services/chargeback_export.py` - Generator CSV chargeback
- `backend/app/api/v1/export.py` - Endpoints streaming chargeback
- `backend/tests/test_chargeback_export.py` - Service + API tests

## Decisions Made

- Intervalo default = mês corrente quando `date_from`/`date_to` ausentes
- `pages_pending` no bucket Páginas pendentes mapeado à coluna mono no CSV

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None.

## Next Phase Readiness

- Pronto para **06-05**: UI Settings Tarifas + coluna custo na auditoria

## Self-Check: PASSED

- FOUND: backend/app/services/chargeback_export.py
- FOUND: backend/tests/test_chargeback_export.py
- FOUND: ef2fc43, cce4296
- Tests: 8 passed (`test_chargeback_export.py`)

---
*Phase: 06-costing-chargeback*
*Completed: 2026-05-27*
