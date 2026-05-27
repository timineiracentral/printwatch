---
phase: 05-master-data-organization
plan: "07"
subsystem: ui
tags: [react-router, settings, crud, registry, import, filterbar, D-08, D-13, D-18]

requires:
  - phase: 05-master-data-organization
    plan: "03"
    provides: Printers CRUD API and unmapped-queues
  - phase: 05-master-data-organization
    plan: "04"
    provides: Org CRUD APIs
  - phase: 05-master-data-organization
    plan: "06"
    provides: CSV import and templates
provides:
  - react-router-dom com / e /settings/* (printers, departments, cost-centers, users, import)
  - Sidebar Jobs + grupo Configurações com 5 NavLinks e ícones lucide
  - CRUD UI modal para 4 entidades com soft-delete
  - Banner unmapped-queues em Impressoras (D-13)
  - ImportPage com download modelo, upload e painel de erros expandível
  - PrinterCombobox migrado para registry (display_name, filtro cups_queue_name normalizado)
affects:
  - phase-06-costing
  - phase-07-manager

tech-stack:
  added: [react-router-dom@6]
  patterns:
    - "SettingsLayout + Outlet no AppShell; JobsPage preserva audit em /"
    - "TanStack Query hooks com invalidate on mutate por entidade"
    - "Dialog modal max-w-lg; tabelas sticky header + zebra"

key-files:
  created:
    - frontend/src/routes/index.tsx
    - frontend/src/pages/JobsPage.tsx
    - frontend/src/pages/settings/PrintersPage.tsx
    - frontend/src/pages/settings/DepartmentsPage.tsx
    - frontend/src/pages/settings/CostCentersPage.tsx
    - frontend/src/pages/settings/UsersPage.tsx
    - frontend/src/pages/settings/ImportPage.tsx
    - frontend/src/api/settings/printers.ts
    - frontend/src/api/settings/departments.ts
    - frontend/src/api/settings/costCenters.ts
    - frontend/src/api/settings/users.ts
    - frontend/src/api/settings/import.ts
    - frontend/src/hooks/usePrintersRegistry.ts
    - frontend/src/hooks/useDepartments.ts
    - frontend/src/hooks/useCostCenters.ts
    - frontend/src/hooks/useUsers.ts
    - frontend/src/components/ui/Dialog.tsx
    - frontend/src/components/settings/UnmappedQueuesBanner.tsx
  modified:
    - frontend/package.json
    - frontend/src/api/client.ts
    - frontend/src/api/printers.ts
    - frontend/src/components/filters/PrinterCombobox.tsx
    - frontend/src/components/layout/Sidebar.tsx
    - frontend/src/types/api.ts

key-decisions:
  - "react-router-dom v6 com BrowserRouter; redirect /settings → printers"
  - "Filtro jobs usa normalizePrinterName(cups_queue_name) para compat com print_jobs.printer"
  - "Combobox exibe display_name; valor interno é fila normalizada"

patterns-established:
  - "api/settings/* espelha endpoints v1; client post/patch/delete/postFormData"
  - "CRUD settings: PageHeader + busca debounced 300ms + dialog + ConfirmDialog desativar"

requirements-completed: [SETTINGS-01, SETTINGS-02, SETTINGS-03, SETTINGS-04, SERVER-04, INV-03, INV-06]

duration: 55min
completed: 2026-05-27
---

# Phase 5 Plan 07: Settings UI Summary

**Settings UI completa com react-router, CRUD modal para quatro entidades, import CSV e FilterBar no registry canônico**

## Performance

- **Duration:** 55 min
- **Started:** 2026-05-27T18:00:00Z
- **Completed:** 2026-05-27T18:55:00Z
- **Tasks:** 4/4 completed
- **Files modified:** 30+

## Accomplishments

- `react-router-dom` com rotas `/` (Jobs audit) e `/settings/*` (5 páginas)
- Sidebar com grupo "Configurações" e ícones Printer, Building2, Wallet, Users, Upload
- API client estendido (POST/PATCH/DELETE/FormData) e hooks TanStack Query por entidade
- Páginas CRUD com dialog modal, soft-delete, busca debounced e textos PT-BR
- Banner amarelo para filas não mapeadas (D-13) com CTA "Cadastrar fila"
- ImportPage: grid 2 colunas, baixar modelo, upload, relatório com erros expandíveis
- `PrinterCombobox` lista registry; exibe `display_name`; filtro jobs usa `cups_queue_name` normalizado
- `npm run build` exit 0

## Task Commits

1. **Task 1: react-router-dom e estrutura de rotas** - `c66d3dc` (feat)
2. **Task 2: API client + hooks CRUD settings** - `06cba71` (feat)
3. **Task 3: Páginas CRUD + unmapped banner + Import** - `8fb2df2` (feat)
4. **Task 4: Migrar PrinterCombobox para registry** - `41b9529` (feat)

**Plan metadata:** `5e8b175` (docs)

## Files Created/Modified

- `frontend/src/routes/index.tsx` — BrowserRouter e rotas Jobs/Settings
- `frontend/src/pages/settings/*.tsx` — CRUD e Import
- `frontend/src/api/settings/*.ts` — clientes REST settings/import
- `frontend/src/components/filters/PrinterCombobox.tsx` — registry + normalização

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## Self-Check: PASSED

- FOUND: frontend/src/routes/index.tsx
- FOUND: frontend/src/pages/settings/PrintersPage.tsx
- FOUND: frontend/src/pages/settings/ImportPage.tsx
- FOUND: commit c66d3dc
- FOUND: commit 06cba71
- FOUND: commit 8fb2df2
- FOUND: commit 41b9529
- `npm run build` exit 0

## Next Phase Readiness

Phase 5 plan 07 complete — all 7/7 plans executed for master-data-organization. Ready for `/gsd-verify-work` on Phase 5 and planning Phase 6 (Costing & Chargeback).
