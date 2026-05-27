---
phase: 04-dashboard-web
plan: "01"
subsystem: ui
tags: [react, vite, tailwind, tanstack-query, vitest, date-fns]

requires: []
provides:
  - frontend/ Vite React 18 + TypeScript scaffold
  - Tailwind v4 + CSS design tokens (04-UI-SPEC)
  - Dev proxy /api → localhost:8000 (D-57)
  - Pure libs filters/dates/media with Vitest Wave 0
affects: [04-02, 04-03, 04-04, 04-05, 04-06, 04-07]

tech-stack:
  added: [react@18, vite@8, tailwindcss@4, @tanstack/react-query@5, vitest@3, date-fns@4, @date-fns/tz]
  patterns: [QueryClientProvider defaults, URL JobFilters round-trip, TZDate presets SP]

key-files:
  created:
    - frontend/package.json
    - frontend/vite.config.ts
    - frontend/vitest.config.ts
    - frontend/src/lib/filters.ts
    - frontend/src/lib/dates.ts
    - frontend/src/lib/media.ts
  modified:
    - frontend/src/main.tsx
    - frontend/src/index.css

key-decisions:
  - "React 18 pinned (not 19) per D-38"
  - "No React Router on placeholder page per D-44"
  - "Vite proxy /api without rewrite preserves /api/v1 path per D-57"

patterns-established:
  - "JobFilters TypeScript mirrors Pydantic JobFilters (D-65)"
  - "Date presets use TZDate.tz America/Sao_Paulo, not browser local Date (D-42)"
  - "formatMediaLabel static map with raw fallback (D-33)"

requirements-completed: [DASH-06]

duration: 5min
completed: 2026-05-27
---

# Phase 4 Plan 01: Frontend Scaffold + Pure Libs Summary

**Vite React 18 scaffold com Tailwind v4, proxy /api, e libs filters/dates/media testadas em Vitest para contratos de URL e timezone SP.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-05-27T13:30:57Z
- **Completed:** 2026-05-27T13:36:00Z
- **Tasks:** 2
- **Files modified:** 21

## Accomplishments

- Projeto `frontend/` criado com React 18, Vite 8, Tailwind v4 (`@tailwindcss/vite`), TanStack Query v5
- Tokens CSS `:root` do 04-UI-SPEC; `QueryClientProvider` com `retry: 1` e `refetchOnWindowFocus: false`
- Proxy dev `/api` → `http://localhost:8000` sem rewrite
- `lib/filters`, `lib/dates`, `lib/media` com 11 testes Vitest verdes

## Task Commits

1. **Task 1: Scaffold frontend Vite React-TS + Tailwind v4 + Query provider** - `4741cf5` (feat)
2. **Task 2: Libs puras + Vitest Wave 0 (filters, dates, media)** - `648e615` (feat)

## Files Created/Modified

- `frontend/vite.config.ts` - React + Tailwind plugins; proxy `/api`
- `frontend/src/main.tsx` - QueryClientProvider
- `frontend/src/index.css` - Tailwind import + semantic tokens
- `frontend/src/lib/filters.ts` - `parseFiltersFromUrl`, `filtersToSearchParams`, `clearFiltersDefaults`
- `frontend/src/lib/dates.ts` - `presetToday`, `presetLast7Days`, `presetMonthToDate` (America/Sao_Paulo)
- `frontend/src/lib/media.ts` - `formatMediaLabel` (A4, Carta, raw fallback)
- `frontend/vitest.config.ts` - jsdom + `@/` alias

## Decisions Made

- React 18.3.x instalado explicitamente (template Vite 9 trazia React 19)
- Página única placeholder sem React Router (D-44)
- Chaves de mídia com caracteres especiais quotadas em `MEDIA_LABELS`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Chave `na_letter_8.5x11in` inválida em objeto literal**
- **Found during:** Task 2 (Vitest)
- **Issue:** Ponto em identificador causava erro de sintaxe esbuild
- **Fix:** Chave quotada `'na_letter_8.5x11in'`
- **Files modified:** `frontend/src/lib/media.ts`
- **Committed in:** `648e615`

**2. [Rule 1 - Bug] `filtersToSearchParams` serializava `search` só com espaços**
- **Found during:** Task 2 (filters.test)
- **Issue:** `search: '  '` gerava param na URL
- **Fix:** Trim antes de `params.set` para username/printer/search
- **Files modified:** `frontend/src/lib/filters.ts`
- **Committed in:** `648e615`

---

**Total deviations:** 2 auto-fixed (2 bugs)
**Impact on plan:** Correções mínimas para testes e sintaxe; sem mudança de escopo.

## Issues Encountered

- Primeiro `npm create vite` no PowerShell gerou template vanilla TS; recriado com `--template react-ts`
- Heredoc de commit não suportado no PowerShell; usado `git commit -m` múltiplo

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Pronto para plan 04-02+ (API client, hooks Query, componentes UI)
- Deploy nginx :80 permanece no plan 04-07

## Self-Check: PASSED

- FOUND: frontend/package.json
- FOUND: frontend/src/lib/filters.ts
- FOUND: frontend/vitest.config.ts
- FOUND: commit 4741cf5
- FOUND: commit 648e615

---
*Phase: 04-dashboard-web*
*Completed: 2026-05-27*
