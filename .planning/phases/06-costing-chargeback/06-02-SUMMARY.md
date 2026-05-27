---
phase: 06-costing-chargeback
plan: "02"
subsystem: api
tags: [costing, decimal, cost-rates, chargeback, fastapi]

requires:
  - phase: 06-costing-chargeback
    plan: "01"
    provides: CostRate model, color_mode normalization
provides:
  - cost_service rate_at, line_cost, aggregate_cost_by_dimension
  - API GET/POST /cost-rates with history and current
affects:
  - 06-03 jobs enrichment and estimated_cost on JobOut
  - 06-04 chargeback CSV exports

tech-stack:
  added: []
  patterns:
    - "Decimal end-to-end for BRL rates (Numeric 12,4)"
    - "rate_at(timestamp) for vigência histórica (D-02)"
    - "Chargeback aggregation exclui outside_policy; printer_id NULL → bucket separado"

key-files:
  created:
    - backend/app/services/cost_service.py
    - backend/app/schemas/cost_rates.py
    - backend/app/api/v1/cost_rates.py
    - backend/tests/test_cost_service.py
    - backend/tests/test_cost_rates.py
  modified:
    - backend/app/api/v1/__init__.py

key-decisions:
  - "aggregate_cost_by_dimension atende COST-04 sem alterar stats_service (D-20)"
  - "Linhas printer_id NULL só no bucket Impressora não cadastrada (D-13)"
  - "color_mode NULL acumula em bucket Páginas pendentes sem custo"

patterns-established:
  - "POST /cost-rates insere vigência; histórico preservado (sem DELETE)"
  - "Sem tarifa: rate_at/line_cost retornam None; agregação usa custo 0"

requirements-completed: [COST-01, COST-02, COST-04]

duration: 35min
completed: 2026-05-27
---

# Phase 6 Plan 02: cost_service + API tarifas Summary

**Read-path de custo com vigência por timestamp, agregação chargeback por CC/dept, e CRUD de tarifas globais em BRL Decimal**

## Performance

- **Duration:** 35 min
- **Started:** 2026-05-27T20:35:00Z
- **Completed:** 2026-05-27T21:10:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments

- `cost_service.py` com `rate_at`, `line_cost`, `format_money_brl`, `aggregate_cost_by_dimension`
- Exclusão `outside_policy` e buckets D-11..D-14 na agregação
- API `/api/v1/cost-rates` (list desc, current, POST nova vigência)
- `stats_service.py` sem import de `cost_service` (grep verificado)

## Task Commits

1. **Task 1: cost_service core** - `1121b2c` (feat)
2. **Task 2: Schemas + router cost-rates** - `47419bb` (feat)

**Plan metadata:** pending (docs commit)

## Files Created/Modified

- `backend/app/services/cost_service.py` - Cálculo e CRUD de tarifas
- `backend/app/schemas/cost_rates.py` - Pydantic Create/Read
- `backend/app/api/v1/cost_rates.py` - Rotas REST
- `backend/app/api/v1/__init__.py` - Registro router `/cost-rates`
- `backend/tests/test_cost_service.py` - Vigência, pending, line_cost
- `backend/tests/test_cost_rates.py` - API histórico e current

## Decisions Made

- Agregação por dimensão no `cost_service` (não em `stats_service`) conforme D-20
- Buckets fixos anexados ao final do resultado quando há dados

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None.

## Next Phase Readiness

- Pronto para **06-03**: enriquecer `JobOut` com páginas faturáveis e `estimated_cost`
- Pronto para **06-04**: `chargeback_export` pode reutilizar `aggregate_cost_by_dimension`

## Self-Check: PASSED

- FOUND: backend/app/services/cost_service.py
- FOUND: backend/app/api/v1/cost_rates.py
- FOUND: backend/tests/test_cost_service.py
- FOUND: backend/tests/test_cost_rates.py
- FOUND: 1121b2c, 47419bb
- Tests: 5 passed (`test_cost_service.py` + `test_cost_rates.py`)

---
*Phase: 06-costing-chargeback*
*Completed: 2026-05-27*
