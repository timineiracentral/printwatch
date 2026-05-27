---
phase: 04-dashboard-web
plan: "02"
subsystem: api
tags: [react, tanstack-query, fetch, url-state, vitest, date-fns]

requires:
  - phase: 04-01
    provides: frontend scaffold, lib/filters, QueryClientProvider, Vite proxy /api
provides:
  - TypeScript types mirroring Pydantic schemas
  - HTTP client and REST modules (jobs, stats, printers, export)
  - TanStack Query hooks with URL-driven filters
  - useDebouncedValue (300ms) for future search field
affects: [04-03, 04-04, 04-05, 04-06]

tech-stack:
  added: []
  patterns:
    - "getJson + ApiError on /api/v1"
    - "URL filters via useSyncExternalStore + replaceState (no React Router)"
    - "useJobs with keepPreviousData for pagination"
    - "stats/summary staleTime 60s — no client-side top aggregation"

key-files:
  created:
    - frontend/src/types/api.ts
    - frontend/src/api/client.ts
    - frontend/src/api/jobs.ts
    - frontend/src/api/stats.ts
    - frontend/src/api/printers.ts
    - frontend/src/api/export.ts
    - frontend/src/hooks/useUrlFilters.ts
    - frontend/src/hooks/useDebouncedValue.ts
    - frontend/src/hooks/useJobs.ts
    - frontend/src/hooks/useStatsSummary.ts
    - frontend/src/hooks/usePrinters.ts
    - frontend/src/lib/format.ts
  modified:
    - frontend/src/lib/filters.ts
    - frontend/src/App.tsx
    - frontend/src/vite-env.d.ts

key-decisions:
  - "JobFilters canonical type in types/api.ts; filters.ts re-exports (D-65)"
  - "exportFiltersToSearchParams omits page/size entirely (D-35)"
  - "ApiError/ExportCapError without parameter properties (erasableSyntaxOnly)"

patterns-established:
  - "ExportFilters = Omit<JobFilters, page | size>"
  - "formatDateTime uses parseISO only — API timestamp already SP (Pitfall 4)"

requirements-completed: [DASH-04, DASH-05, DASH-06]

duration: 8min
completed: 2026-05-27
---

# Phase 4 Plan 02: Data Layer + Query Hooks Summary

**Tipos espelhando Pydantic, cliente HTTP `/api/v1`, hooks TanStack Query com filtros na URL e debounce 300ms — prontos para os componentes de UI.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-05-27T13:36:00Z
- **Completed:** 2026-05-27T13:44:00Z
- **Tasks:** 2
- **Files modified:** 16

## Accomplishments

- `types/api.ts` com `JobOut`, `Page<T>`, `StatsSummaryResponse` alinhados ao backend
- Cliente `getJson` + `ApiError`; módulos jobs/stats/printers/export (CSV sem page/size, `ExportCapError` em 400)
- `useUrlFilters` com `useSyncExternalStore` e `history.replaceState` (sem react-router)
- `useJobs` + `keepPreviousData`; `useStatsSummary` staleTime 60s; `usePrinters` staleTime 5min
- `useDebouncedValue` testado com fake timers; `lib/format.ts` para pt-BR e datetime
- App smoke exibe `jobs.total` e `stats.hoje.jobs` via JSON (removido no plan 06)

## Task Commits

1. **Task 1: Tipos TypeScript + api/client + módulos REST** - `67d66af` (feat)
2. **Task 2: useUrlFilters + debounce + hooks Query** - `1162812` (feat)

## Files Created/Modified

- `frontend/src/types/api.ts` - Contratos API TypeScript
- `frontend/src/api/client.ts` - `baseUrl`, `getJson`, `ApiError`
- `frontend/src/api/export.ts` - `downloadCsv`, `ExportCapError`, params sem paginação
- `frontend/src/hooks/useUrlFilters.ts` - Estado de filtros na URL
- `frontend/src/hooks/useJobs.ts` - Query jobs com placeholderData
- `frontend/src/lib/format.ts` - Formatação pt-BR para cards e tabela

## Decisions Made

- Tipos movidos para `types/api.ts`; `filters.ts` importa e re-exporta `JobFilters`
- Classes de erro sem parameter properties por `erasableSyntaxOnly` no tsconfig
- `setFilters` reseta `page` para 1 quando filtros de conteúdo mudam

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Parameter properties incompatíveis com erasableSyntaxOnly**
- **Found during:** Task 1 (build)
- **Issue:** TS1294 em `ApiError` e `ExportCapError`
- **Fix:** Propriedades explícitas `readonly status/detail`
- **Files modified:** `frontend/src/api/client.ts`, `frontend/src/api/export.ts`
- **Committed in:** `67d66af`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Ajuste de sintaxe TypeScript; sem mudança de escopo.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Known Stubs

| File | Stub | Resolvido em |
|------|------|--------------|
| `frontend/src/App.tsx` | Smoke JSON temporário (não é UI final) | Plan 04-06 |

## Next Phase Readiness

- Plans 03–06 podem consumir `useUrlFilters`, `useJobs`, `useStatsSummary`, `usePrinters`, `downloadCsv`
- Integrar `useDebouncedValue` no campo search da barra de filtros (plan 05)
- Remover smoke de `App.tsx` no plan 06

## Self-Check: PASSED

- FOUND: frontend/src/types/api.ts
- FOUND: frontend/src/hooks/useUrlFilters.ts
- FOUND: frontend/src/hooks/useDebouncedValue.test.ts
- FOUND: commit 67d66af
- FOUND: commit 1162812

---
*Phase: 04-dashboard-web*
*Completed: 2026-05-27*
