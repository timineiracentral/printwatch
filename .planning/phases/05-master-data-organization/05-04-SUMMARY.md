---
phase: 05-master-data-organization
plan: "04"
subsystem: api
tags: [departments, cost-centers, users, crud, org-api, soft-delete, D-15, D-16, D-17]

requires:
  - phase: 05-master-data-organization
    plan: "01"
    provides: Schema departments, cost_centers, users
  - phase: 05-master-data-organization
    plan: "02"
    provides: normalize_org_code
provides:
  - CRUD /api/v1/departments, /cost-centers, /users
  - Org services com unicidade case-insensitive de code
  - users.cups_username imutável após create; filtros de listagem
affects:
  - 05-05-matcher
  - 05-06-import
  - 05-07-settings-ui

tech-stack:
  added: []
  patterns:
    - "Entidades org independentes (D-15); dept referencia CC opcional ativo"
    - "List org com q e include_inactive; users com department_id, cost_center_id, q"
    - "UserUpdate sem cups_username — imutabilidade via schema"

key-files:
  created:
    - backend/app/schemas/cost_center.py
    - backend/app/schemas/department.py
    - backend/app/schemas/user.py
    - backend/app/services/cost_centers_service.py
    - backend/app/services/departments_service.py
    - backend/app/services/users_service.py
    - backend/app/api/v1/cost_centers.py
    - backend/app/api/v1/departments.py
    - backend/app/api/v1/users.py
    - backend/tests/test_org_api.py
  modified:
    - backend/app/api/v1/__init__.py

key-decisions:
  - "code dept/CC normalizado UPPERCASE; duplicata detectada case-insensitive"
  - "FK cost_center_id e department_id validam existência e is_active"
  - "cups_username preserva casing do CUPS; unicidade exata após strip"

patterns-established:
  - "Mesmo padrão printers_service: soft-delete, 409 duplicado, 422 FK inativa"
  - "Sem user_id em print_jobs (D-07)"

requirements-completed: [ORG-01, ORG-02, ORG-03, ORG-04, ORG-05, ORG-06, ORG-07, ORG-08, ORG-09]

duration: 25min
completed: 2026-05-27
---

# Phase 5 Plan 04: Org APIs Summary

**CRUD independente para departments, cost-centers e users com normalização UPPERCASE de códigos, soft-delete e filtros de listagem documentados no OpenAPI**

## Performance

- **Duration:** 25 min
- **Started:** 2026-05-27T16:00:00Z
- **Completed:** 2026-05-27T16:25:00Z
- **Tasks:** 2/2 completed
- **Files modified:** 10

## Accomplishments

- Routers `/api/v1/cost-centers`, `/departments`, `/users` registrados no api_v1_router
- `normalize_org_code` em create/update; POST `"fin"` persiste `"FIN"`; duplicata → 409
- Users: `department_id` obrigatório no create; `cups_username` fora de `UserUpdate`
- List users com `department_id`, `cost_center_id`, `q`, `include_inactive` no OpenAPI
- 11 testes em `test_org_api.py`; suite completa 102 passed

## Task Commits

Each task was committed atomically:

1. **Task 1: Cost centers e departments CRUD** - `402bf19` (feat)
2. **Task 2: Users CRUD** - `93d48f2` (feat)

**Plan metadata:** pending (docs commit)

## Files Created/Modified

- `backend/app/schemas/cost_center.py` - CostCenterCreate/Update/Read
- `backend/app/schemas/department.py` - DepartmentCreate/Update/Read
- `backend/app/schemas/user.py` - UserCreate/Update/Read (sem cups_username no update)
- `backend/app/services/cost_centers_service.py` - CRUD CC, q, include_inactive
- `backend/app/services/departments_service.py` - CRUD dept, valida CC ativo
- `backend/app/services/users_service.py` - CRUD users, filtros, FK validation
- `backend/app/api/v1/cost_centers.py` - Endpoints REST
- `backend/app/api/v1/departments.py` - Endpoints REST
- `backend/app/api/v1/users.py` - Endpoints REST com query params
- `backend/tests/test_org_api.py` - CRUD, 409, filtros, OpenAPI

## Decisions Made

- `include_inactive` (default false) alinhado ao plano; espelha semântica de active_only em printers
- `cups_username` strip apenas; sem uppercase — match exato ao log CUPS (D-17)
- Department com `cost_center_id` opcional rejeita CC soft-deleted

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None

## Next Phase Readiness

- Plan 05-05 (matcher) pode consumir registry printers; org APIs prontas para import (05-06) e Settings UI (05-07)
- Wave 2 completa: 05-02, 05-03, 05-04

## Self-Check: PASSED

- FOUND: backend/app/api/v1/departments.py
- FOUND: backend/app/api/v1/cost_centers.py
- FOUND: backend/app/api/v1/users.py
- FOUND: backend/tests/test_org_api.py
- FOUND: commit 402bf19
- FOUND: commit 93d48f2
