---
phase: 06-costing-chargeback
plan: "05"
subsystem: ui
tags: [costing, chargeback, react, settings, jobs, tarifas]

requires:
  - phase: 06-costing-chargeback
    plan: "03"
    provides: JobOut cost fields, GET/PATCH /jobs/lines
  - phase: 06-costing-chargeback
    plan: "04"
    provides: chargeback CSV export endpoints
provides:
  - CostRatesPage Settings Tarifas (vigência, histórico, BRL)
  - Jobs coluna custo estimado com toggle localStorage
  - ColorModeCorrectionModal para admin
  - ChargebackExportButtons na JobsPage
affects:
  - phase 07 manager dashboard (stats unchanged)

tech-stack:
  added: []
  patterns:
    - "printwatch.showCostColumn em localStorage (default false)"
    - "Chargeback export via window.open com query dos filtros Jobs"
    - "formatBrl pt-BR 2 casas decimais"

key-files:
  created:
    - frontend/src/pages/settings/CostRatesPage.tsx
    - frontend/src/api/settings/costRates.ts
    - frontend/src/hooks/useCostRates.ts
    - frontend/src/hooks/useShowCostColumn.ts
    - frontend/src/components/jobs/ColorModeCorrectionModal.tsx
    - frontend/src/components/export/ChargebackExportButtons.tsx
  modified:
    - frontend/src/components/jobs/JobsTable.tsx
    - frontend/src/pages/JobsPage.tsx
    - frontend/src/types/api.ts
    - frontend/src/routes/index.tsx
    - frontend/src/components/layout/Sidebar.tsx
    - frontend/src/api/jobs.ts
    - frontend/src/lib/format.ts

key-decisions:
  - "Toggle custo na JobsPage (não em /stats); sem alteração em rotas manager"
  - "Exports chargeback na JobsPage para reutilizar date_from/date_to dos filtros URL"
  - "Correção manual via modal por grupo agregado (minute_bucket obrigatório)"

patterns-established:
  - "Tarifas: POST nova vigência + tabela histórico desc"
  - "Custo est. exibe — quando estimated_cost null"

requirements-completed: [COST-01, COST-03, CHRG-01, CHRG-02]

duration: 35min
completed: 2026-05-27
---

# Phase 6 Plan 05: UI Tarifas, custo Jobs e chargeback Summary

**Settings Tarifas com histórico BRL, coluna de custo opcional na auditoria, correção manual mono/color e downloads chargeback por CC/departamento**

## Performance

- **Duration:** 35 min
- **Started:** 2026-05-27T22:30:00Z
- **Completed:** 2026-05-27T23:05:00Z
- **Tasks:** 3
- **Files modified:** 13

## Accomplishments

- `CostRatesPage` em `/settings/cost-rates` com tarifa vigente, formulário de nova vigência e histórico
- Sidebar com link **Tarifas** (ícone Coins)
- `JobsTable` com toggle `printwatch.showCostColumn`, coluna **Custo est.** e badge de páginas pendentes
- `ColorModeCorrectionModal` com GET `/jobs/lines` e PATCH `color-mode` por linha
- `ChargebackExportButtons` na `JobsPage` abrindo CSV por centro de custo e departamento
- `npm run build` (frontend) exit 0

## Task Commits

1. **Task 1: API client + CostRatesPage** - `47ba000` (feat)
2. **Task 2: Jobs custo + correção manual** - `9d688cc` (feat)
3. **Task 3: Links export chargeback** - `6c84f7d` (feat)
4. **Fix Badge TS** - `5c1b838` (fix)

**Plan metadata:** `f3d0dd6` (docs: complete plan)

## Files Created/Modified

- `frontend/src/pages/settings/CostRatesPage.tsx` - UI tarifas D-03
- `frontend/src/api/settings/costRates.ts` - Client REST cost-rates
- `frontend/src/hooks/useCostRates.ts` - React Query list/current/create
- `frontend/src/components/jobs/JobsTable.tsx` - Coluna custo + ações correção
- `frontend/src/components/jobs/ColorModeCorrectionModal.tsx` - Modal D-08
- `frontend/src/components/export/ChargebackExportButtons.tsx` - Downloads CHRG
- `frontend/src/hooks/useShowCostColumn.ts` - Persistência localStorage D-10

## Decisions Made

- Exports chargeback colocados na JobsPage (não Tarifas) para herdar filtros de período da URL
- Sem gate de role no frontend para correção manual (API aberta como demais rotas admin da fase)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] TypeScript: Badge children array e className inválido**
- **Found during:** Verificação `npm run build` pós Task 2
- **Issue:** TS2322 em JobsTable e CostRatesPage
- **Fix:** Template string no Badge pendente; wrapper span para Badge Vigente
- **Files modified:** `JobsTable.tsx`, `CostRatesPage.tsx`, `useShowCostColumn.ts`
- **Commit:** fix após task 3

---

**Total deviations:** 1 auto-fixed (Rule 1)
**Impact on plan:** Correções de tipo; comportamento conforme plano.

## Issues Encountered

None blocking.

## User Setup Required

None.

## Next Phase Readiness

- Fase 06 UI completa; pronta para verificação UAT e Fase 07 (`/manager`) sem custo em `/stats`

## Self-Check: PASSED

- FOUND: frontend/src/pages/settings/CostRatesPage.tsx
- FOUND: frontend/src/components/jobs/ColorModeCorrectionModal.tsx
- FOUND: frontend/src/components/export/ChargebackExportButtons.tsx
- FOUND: 47ba000, 9d688cc, 6c84f7d
- Build: `npm run build` exit 0

---
*Phase: 06-costing-chargeback*
*Completed: 2026-05-27*
