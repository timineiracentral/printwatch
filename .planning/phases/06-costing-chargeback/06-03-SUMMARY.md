---
phase: 06-costing-chargeback
plan: "03"
subsystem: api
tags: [costing, jobs, billable-pages, color-mode, fastapi, chargeback]

requires:
  - phase: 06-costing-chargeback
    plan: "02"
    provides: cost_service rate_at and line_cost
provides:
  - JobOut pages_billable, pages_pending_color, pages_mono, pages_color, estimated_cost
  - GET /api/v1/jobs/lines for raw print_jobs in a group
  - PATCH /api/v1/jobs/lines/{id}/color-mode with source manual
affects:
  - 06-04 chargeback CSV exports
  - 06-05 frontend JobsTable cost column and manual correction UI

tech-stack:
  added: []
  patterns:
    - "SQL CASE sums for mono/color/pending in aggregated jobs query"
    - "estimated_cost enriched post-aggregation via cost_service per group lines"
    - "Routes /lines registered before /{job_id} in FastAPI router"

key-files:
  created:
    - backend/app/schemas/job_lines.py
    - backend/tests/test_jobs_cost.py
    - backend/tests/test_jobs_color_patch.py
  modified:
    - backend/app/services/jobs_service.py
    - backend/app/schemas/jobs.py
    - backend/app/api/v1/jobs.py

key-decisions:
  - "estimated_cost calculado em Python com cache rate_at por timestamp (batch por grupo)"
  - "minute_bucket exposto em JobOut para UI chamar GET /lines com chave exata"
  - "stats_service.py permanece sem campos de custo (D-20)"

patterns-established:
  - "Correção manual: PATCH define color_mode_source=manual; GET jobs subsequente recalcula custo"
  - "Linhas sem color_mode não entram em pages_billable nem estimated_cost"

requirements-completed: [COST-02, COST-03]

duration: 25min
completed: 2026-05-27
---

# Phase 6 Plan 03: Jobs API cost metrics + manual color patch Summary

**JobOut com páginas faturáveis e custo estimado; GET de linhas brutas por grupo; PATCH mono/color com source manual**

## Performance

- **Duration:** 25 min
- **Started:** 2026-05-27T21:15:00Z
- **Completed:** 2026-05-27T21:40:00Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- Agregação SQL com `pages_mono`, `pages_color`, `pages_pending_color`, `pages_billable`
- `estimated_cost` somando `line_cost` das linhas classificadas do grupo
- `GET /api/v1/jobs/lines` com chaves de agrupamento obrigatórias (422 se faltar)
- `PATCH /api/v1/jobs/lines/{line_id}/color-mode` com `color_mode_source=manual`
- `stats_service.py` sem `estimated_cost` (verificado em teste)

## Task Commits

1. **Task 1: Agregação billable + estimated_cost** - `b7acaad` (feat)
2. **Task 2+3: GET linhas + PATCH color-mode** - `6fa965f` (feat)

**Plan metadata:** `9dbaed0` (docs: complete plan)

## Files Created/Modified

- `backend/app/services/jobs_service.py` - CASE aggregates, cost enrichment, list/patch lines
- `backend/app/schemas/jobs.py` - JobOut cost fields + minute_bucket
- `backend/app/schemas/job_lines.py` - JobLineOut, JobLineFilters, ColorModePatch
- `backend/app/api/v1/jobs.py` - /lines e PATCH antes de /{job_id}
- `backend/tests/test_jobs_cost.py` - 2 mono + 1 NULL, estimated_cost com tarifa
- `backend/tests/test_jobs_color_patch.py` - PATCH recalcula agregado

## Decisions Made

- `estimated_cost` retorna `null` quando não há tarifa ou nenhuma linha faturável teve custo calculável
- `minute_bucket` no detalhe GET by id definido em Python (evita `literal()` incompatível com SQLite)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] SQLite não suporta `func.literal` em get_job_by_id**
- **Found during:** Task 1 (verificação test_api_jobs)
- **Issue:** `OperationalError: no such function: literal`
- **Fix:** `minute_bucket` atribuído no dict Python após a query agregada
- **Files modified:** `backend/app/services/jobs_service.py`
- **Committed in:** `b7acaad`

---

**Total deviations:** 1 auto-fixed (Rule 1)
**Impact on plan:** Correção mínima; comportamento alinhado ao plano.

## Issues Encountered

None beyond SQLite literal fix.

## User Setup Required

None.

## Next Phase Readiness

- Pronto para **06-04**: exports chargeback podem reutilizar padrões de custo
- Pronto para **06-05**: UI pode consumir `JobOut.estimated_cost`, `pages_pending_color`, `GET/PATCH /jobs/lines`

## Self-Check: PASSED

- FOUND: backend/app/services/jobs_service.py
- FOUND: backend/app/schemas/job_lines.py
- FOUND: backend/tests/test_jobs_cost.py
- FOUND: backend/tests/test_jobs_color_patch.py
- FOUND: b7acaad, 6fa965f
- Tests: 20 passed (test_jobs_cost + test_jobs_color_patch + test_api_jobs)

---
*Phase: 06-costing-chargeback*
*Completed: 2026-05-27*
