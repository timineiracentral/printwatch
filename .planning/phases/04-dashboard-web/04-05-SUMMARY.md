---
phase: 04-dashboard-web
plan: "05"
subsystem: ui
tags: [react, headless-ui, tanstack-query, filters, table, pagination, pt-BR]

requires:
  - phase: 04-02
    provides: useUrlFilters, useJobs, useDebouncedValue, lib/dates e filters
  - phase: 04-03
    provides: Button, Input, Skeleton, EmptyState, ErrorBanner
  - phase: 04-04
    provides: SummaryCards no dashboard

provides:
  - FilterBar com presets, datas, usuário, impressora, busca por arquivo
  - JobsTable 7 colunas com paginação server-side
  - JobsPagination com meta pt-BR e seletor 50/100

affects: [04-06]

tech-stack:
  added: []
  patterns:
    - "Filtros na URL via useUrlFilters; refetch TanStack Query em filter change"
    - "Busca por arquivo com useDebouncedValue(300ms) antes de setFilters"
    - "PrinterCombobox Headless UI — match exato, sem free text"
    - "Tabela: opacity 0.6 + barra indeterminada no refetch; skeleton 8 linhas no load inicial"

key-files:
  created:
    - frontend/src/components/filters/DatePresetGroup.tsx
    - frontend/src/components/filters/PrinterCombobox.tsx
    - frontend/src/components/filters/FilterBar.tsx
    - frontend/src/components/jobs/JobsTable.tsx
    - frontend/src/components/jobs/JobsPagination.tsx
  modified:
    - frontend/src/App.tsx
    - frontend/src/lib/filters.ts
    - frontend/src/index.css

key-decisions:
  - "Seletor de page size 50/100 na paginação — sem complexidade extra além do select"
  - "hasActiveFilters em lib/filters para empty state filtrado vs. vazio global"

patterns-established:
  - "Dashboard vertical slice: SummaryCards → FilterBar → JobsTable → JobsPagination"
  - "Preset Mês atual na barra ≠ bucket stats.mes nos cards (comentário em FilterBar)"

requirements-completed: [DASH-03, DASH-04, DASH-05, DASH-06]

duration: 25min
completed: 2026-05-27
---

# Phase 4 Plan 05: FilterBar + JobsTable Summary

**Barra de filtros sincronizada com a URL e tabela de jobs paginada server-side — centro visual do dashboard com debounce, combobox e estados loading/empty/erro.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-05-27T13:30:00Z
- **Completed:** 2026-05-27T13:55:00Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- `DatePresetGroup` com pills Hoje / Últimos 7 dias / Mês atual (`--accent-tint` ativo)
- `FilterBar` sempre visível: datas De/Até, usuário, `PrinterCombobox`, arquivo com debounce 300ms, Limpar filtros
- `JobsTable` com 7 colunas (`formatDateTime`, `formatMediaLabel`), sticky header, zebra, truncate + tooltip em username
- Paginação server-side via `useJobs(filters)` — sem filtro client-side no dataset
- `JobsPagination`: "Mostrando {from}–{to} de {total} jobs", prev/next, size 50/100
- `App.tsx` ordem D-06/D-48 com área flex-1 para a tabela
- `npm run build` e `vitest` OK

## Task Commits

1. **Task 1: FilterBar — presets, datas, usuário, impressora, search debounced** - `cdde7b4` (feat)
2. **Task 2: JobsTable + JobsPagination + estados loading/empty** - `bfd035f` (feat)

## Files Created/Modified

- `frontend/src/components/filters/DatePresetGroup.tsx` — pills de preset com detecção de ativo
- `frontend/src/components/filters/PrinterCombobox.tsx` — @headlessui/react Combobox, typeahead client-side
- `frontend/src/components/filters/FilterBar.tsx` — barra completa + comentário preset vs. stats.mes
- `frontend/src/components/jobs/JobsTable.tsx` — tabela semântica, skeleton, refetch UI, empty/error
- `frontend/src/components/jobs/JobsPagination.tsx` — meta label e controles de página
- `frontend/src/lib/filters.ts` — `hasActiveFilters` para empty state
- `frontend/src/App.tsx` — integração vertical slice
- `frontend/src/index.css` — animação barra de progresso no refetch

## Decisions Made

- Seletor 50/100 itens por página incluído na paginação (opcional do plano, baixa complexidade)
- `hasActiveFilters` centralizado em `lib/filters` em vez de lógica duplicada na tabela

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Verificação `curl` contra `localhost/api/v1/jobs` não executada (API/nginx indisponível neste ambiente Windows local).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- DASH-03/04/05/06 entregues na UI; pronto para plan 06 (export CSV)
- Botão Exportar CSV permanece disabled até plan 06

## Self-Check: PASSED

- FOUND: `frontend/src/components/filters/FilterBar.tsx`
- FOUND: `frontend/src/components/jobs/JobsTable.tsx`
- FOUND: commit `cdde7b4`
- FOUND: commit `bfd035f`

---
*Phase: 04-dashboard-web*
*Completed: 2026-05-27*
