---
phase: 04-dashboard-web
plan: "04"
subsystem: ui
tags: [react, tanstack-query, summary-cards, pt-BR, dashboard]

requires:
  - phase: 04-02
    provides: useStatsSummary, formatTopLabel, StatsSummaryResponse types
  - phase: 04-03
    provides: AppShell, PageHeader, Skeleton, ErrorBanner

provides:
  - SummaryCard metric/top variants
  - SummaryCards grid com loading, empty, error
  - Dashboard com primeiro dado real (DASH-02)

affects: [04-05, 04-06]

tech-stack:
  added: []
  patterns:
    - "Tops exclusivamente de mes.top_users[0] e mes.top_printers[0] — sem agregação client-side"
    - "Skeleton 4 cards só no isLoading inicial; stale data em refetch"
    - "Grid 2 col (lg) / 4 col (xl), gap 16px"

key-files:
  created:
    - frontend/src/components/summary/SummaryCard.tsx
    - frontend/src/components/summary/SummaryCards.tsx
  modified:
    - frontend/src/App.tsx
    - frontend/src/components/layout/PageHeader.tsx

key-decisions:
  - "PageHeader mb-6 (24px) para espaçamento D-06 entre título e cards"
  - "Métricas hoje usam formatNumberPtBr; tops usam formatTopLabel"

patterns-established:
  - "SummaryCard: border --border, radius 12px, shadow mínima UI-SPEC"
  - "Empty top: Sem dados no período sem ícone (card variant)"

requirements-completed: [DASH-02]

duration: 15min
completed: 2026-05-27
---

# Phase 4 Plan 04: Summary Cards Summary

**Quatro cards do dashboard alimentados por GET /api/v1/stats/summary — jobs/páginas hoje e tops do mês em pt-BR com skeleton, vazio e erro.**

## Performance

- **Duration:** 15 min
- **Started:** 2026-05-27T15:00:00Z
- **Completed:** 2026-05-27T15:15:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- `SummaryCard` com variantes `metric` (24px) e `top` (linha única formatada)
- `SummaryCards` usa `useStatsSummary`, skeleton ×4 no loading, `ErrorBanner` + refetch no erro
- Labels pt-BR: Jobs hoje, Páginas hoje, Top usuário do mês, Top impressora do mês
- `App.tsx` renderiza cards abaixo do `PageHeader` com placeholder para filtros/tabela (plan 05)
- Build frontend (`npm run build`) OK

## Task Commits

1. **Task 1: SummaryCard + SummaryCards com loading/empty/error** - `45e43b1` (feat)
2. **Task 2: Integrar SummaryCards no App abaixo do PageHeader** - `58a38fb` (feat)

## Files Created/Modified

- `frontend/src/components/summary/SummaryCard.tsx` — card metric/top, empty copy
- `frontend/src/components/summary/SummaryCards.tsx` — grid, hook, estados
- `frontend/src/App.tsx` — wire SummaryCards + placeholder plan 05
- `frontend/src/components/layout/PageHeader.tsx` — `mb-6` para gap 24px (D-06)

## Decisions Made

- `PageHeader` margin inferior ajustada de 32px para 24px para cumprir espaçamento header → cards sem wrapper extra no `App`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] PageHeader spacing 24px**
- **Found during:** Task 2 (integração App)
- **Issue:** `PageHeader` usava `mb-8` (32px); plano e D-06 exigem 24px entre header e cards
- **Fix:** `mb-8` → `mb-6` em `PageHeader.tsx`
- **Files modified:** `frontend/src/components/layout/PageHeader.tsx`
- **Verification:** Tailwind `mb-6` = 1.5rem = 24px
- **Committed in:** `58a38fb`

---

**Total deviations:** 1 auto-fixed (1 missing critical spacing)
**Impact on plan:** Ajuste visual mínimo; sem mudança de escopo funcional.

## Issues Encountered

- Verificação `curl` contra `localhost/api/v1/stats/summary` não executada neste ambiente (API/nginx não disponível localmente); validação manual pendente com stack deployada (plan 06).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- DASH-02 entregue na UI; pronto para plan 05 (FilterBar + JobsTable)
- Placeholder em `App.tsx` marca slot para filtros e tabela
- Exportar CSV continua disabled até plan 06

## Self-Check: PASSED

- FOUND: `frontend/src/components/summary/SummaryCard.tsx`
- FOUND: `frontend/src/components/summary/SummaryCards.tsx`
- FOUND: commit `45e43b1`
- FOUND: commit `58a38fb`

---
*Phase: 04-dashboard-web*
*Completed: 2026-05-27*
