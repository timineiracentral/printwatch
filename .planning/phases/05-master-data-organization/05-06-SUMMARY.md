---
phase: 05-master-data-organization
plan: "06"
subsystem: api
tags: [csv, import, bulk, templates, multipart, D-23, D-24, D-25, D-26]

requires:
  - phase: 05-master-data-organization
    plan: "03"
    provides: Printers CRUD API and normalize_printer_name
  - phase: 05-master-data-organization
    plan: "04"
    provides: Org CRUD APIs and normalize_org_code
provides:
  - POST /api/v1/import/{entity} multipart CSV with per-line report
  - GET /api/v1/import/templates/{entity} text/csv attachment
  - import_service upsert by natural key (code, cups_username, cups_queue_name)
  - strict=false partial commit; strict=true all-or-nothing rollback
affects:
  - 05-07-settings-ui

tech-stack:
  added: [python-multipart]
  patterns:
    - "CSV utf-8-sig parse; dept/CC codes UPPERCASE on import"
    - "ImportResult JSON: total, created, updated, skipped, errors[{line, message}]"
    - "Formula injection mitigation: prefix ' on =+-@ fields"

key-files:
  created:
    - backend/app/import_templates/departments.csv
    - backend/app/import_templates/cost_centers.csv
    - backend/app/import_templates/users.csv
    - backend/app/import_templates/printers.csv
    - backend/app/api/v1/import_routes.py
    - backend/app/services/import_service.py
    - backend/tests/test_import_csv.py
  modified:
    - backend/requirements.txt

key-decisions:
  - "strict=false (default) commits each valid row; strict=true rolls back on any validation error"
  - "Upsert resolves department_code and cost_center_code to FK ids; skips when unchanged"
  - "Upload limit 5MB; python-multipart required for FastAPI UploadFile"

patterns-established:
  - "Static templates in backend/app/import_templates/ served via FileResponse"
  - "Import handlers mirror org/printer validation without per-row HTTPException"

requirements-completed: [IMPORT-01, IMPORT-02, IMPORT-03, IMPORT-04, IMPORT-05]

duration: 35min
completed: 2026-05-27
---

# Phase 5 Plan 06: CSV Import Bulk Summary

**Import CSV bulk com relatório por linha, templates downloadáveis, partial commit por padrão e rollback total em strict=true**

## Performance

- **Duration:** 35 min
- **Started:** 2026-05-27T17:00:00Z
- **Completed:** 2026-05-27T17:35:00Z
- **Tasks:** 2/2 completed
- **Files modified:** 8

## Accomplishments

- Templates estáticos para departments, cost-centers, users e printers
- `GET /api/v1/import/templates/{entity}` retorna `text/csv` com `Content-Disposition: attachment`
- `POST /api/v1/import/{entity}` aceita multipart CSV; entidades `printers|departments|cost-centers|users`
- Resposta JSON com `total`, `created`, `updated`, `skipped`, `errors[{line, message}]`
- Modo `strict=true` faz rollback total se qualquer linha falhar; default persiste linhas válidas
- Códigos dept/CC normalizados UPPERCASE no import (D-26)
- 5 testes em `test_import_csv.py` passando

## Task Commits

1. **Task 1: Templates CSV estáticos** - `7ee1e83` (feat)
2. **Task 2: Import service e rota POST** - `50299ce` (feat)

**Plan metadata:** pending (docs commit)

## Files Created/Modified

- `backend/app/import_templates/*.csv` - Cabeçalhos por entidade (D-25)
- `backend/app/api/v1/import_routes.py` - GET templates + POST import
- `backend/app/services/import_service.py` - Parse, validação, upsert, strict/partial
- `backend/tests/test_import_csv.py` - Partial 48/50, strict rollback, normalize, 413
- `backend/requirements.txt` - python-multipart para UploadFile

## Decisions Made

- Upsert por natural key evita duplicatas; contadores created/updated/skipped refletem mutação real
- Referências CSV usam `department_code` / `cost_center_code` (não IDs) para operadores de TI
- Sanitização de formula injection prefixa `'` em valores que começam com `=+-@`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] python-multipart ausente para UploadFile**
- **Found during:** Task 2 (POST import route)
- **Issue:** FastAPI exige python-multipart para multipart/form-data; app não importava
- **Fix:** Adicionado `python-multipart==0.0.20` em requirements.txt
- **Files modified:** backend/requirements.txt
- **Verification:** `pytest tests/test_import_csv.py -q` — 5 passed
- **Committed in:** 50299ce

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Dependência legítima para upload CSV; sem scope creep.

## Issues Encountered

None beyond missing python-multipart (handled via Rule 3).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Import API pronta para Settings UI (05-07) — download template, upload, painel de resultado
- Org e printer CRUD já disponíveis como dependência de FK/código no CSV

## Self-Check: PASSED

- FOUND: backend/app/import_templates/departments.csv
- FOUND: backend/app/api/v1/import_routes.py
- FOUND: backend/app/services/import_service.py
- FOUND: backend/tests/test_import_csv.py
- FOUND: commit 7ee1e83
- FOUND: commit 50299ce

---
*Phase: 05-master-data-organization*
*Completed: 2026-05-27*
