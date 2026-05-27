---
phase: 05-master-data-organization
plan: "01"
subsystem: database
tags: [alembic, sqlalchemy, sqlite, migrations, cors, wal]

requires:
  - phase: 03-backend-api
    provides: FastAPI app, print_jobs schema, session layer
  - phase: 04-dashboard-web
    provides: CORS origins config, frontend dev setup
provides:
  - Alembic migration framework in backend/alembic/
  - Master tables printers, departments, cost_centers, users
  - print_jobs.printer_id nullable FK
  - Partial index idx_print_jobs_printer_id_null for matcher
  - CORS write methods (POST, PATCH, PUT, DELETE)
  - SQLite WAL mode on startup
affects:
  - 05-02-normalize
  - 05-03-crud-printers
  - 05-04-crud-org
  - 05-05-matcher

tech-stack:
  added: [alembic==1.15.2]
  patterns:
    - Alembic batch_alter_table for SQLite ALTER on print_jobs
    - Conditional migration bootstrap for empty DB vs v1.0 existing DB
    - ensure_wal_mode in FastAPI lifespan after ensure_indexes

key-files:
  created:
    - backend/alembic.ini
    - backend/alembic/env.py
    - backend/alembic/versions/085a2d5c5767_master_data_tables.py
    - backend/tests/test_migrations.py
  modified:
    - backend/app/db/models.py
    - backend/app/db/migrations.py
    - backend/app/main.py
    - backend/requirements.txt
    - .env.example
    - backend/tests/conftest.py

key-decisions:
  - "Migration condicional: cria print_jobs completo em DB vazio; batch_alter em DB v1.0"
  - "env.py lê DB_PATH de os.environ em runtime (não settings cacheado)"
  - "RUN_MIGRATIONS_ON_STARTUP=false — migrations via comando explícito, não no watcher"

patterns-established:
  - "Alembic render_as_batch=True em env.py para SQLite"
  - "Master entities com is_active, created_at, updated_at obrigatórios"

requirements-completed: [DATA-04, DATA-05, DATA-06, DATA-07]

duration: 25min
completed: 2026-05-27
---

# Phase 5 Plan 01: Schema Foundation Summary

**Alembic migrations with master data tables (printers, departments, cost_centers, users), nullable printer_id FK on print_jobs, CORS write methods, and SQLite WAL on startup**

## Performance

- **Duration:** 25 min
- **Started:** 2026-05-27T15:00:00Z
- **Completed:** 2026-05-27T15:25:00Z
- **Tasks:** 4/4 completed
- **Files modified:** 11

## Accomplishments

- Alembic inicializado em `backend/alembic/` com `target_metadata` e URL dinâmica via `DB_PATH`
- Modelos SQLAlchemy Printer, Department, CostCenter, User + `PrintJob.printer_id` nullable FK
- Revision `085a2d5c5767` com `batch_alter_table` para SQLite e índice parcial para matcher
- CORS expandido para métodos de escrita; WAL habilitado no lifespan; `RUN_MIGRATIONS_ON_STARTUP` documentado
- Testes de migration cobrindo DB vazio, DB v1.0, downgrade/reupgrade

## Task Commits

Each task was committed atomically:

1. **Task 1: Inicializar Alembic e dependência** - `dfbe4fa` (chore)
2. **Task 2: Modelos SQLAlchemy e revision inicial** - `bba697c` (feat)
3. **Task 3: CORS, WAL e lifespan hook para migrations** - `849dd7b` (feat)
4. **Task 4: Schema push — alembic upgrade head** - `2c0f054` (test)

**Plan metadata:** pending (docs commit)

## Files Created/Modified

- `backend/alembic/env.py` - Metadata, render_as_batch, DB_PATH runtime
- `backend/alembic/versions/085a2d5c5767_master_data_tables.py` - Master tables + printer_id
- `backend/app/db/models.py` - Entidades mestre e printer_id em PrintJob
- `backend/app/db/migrations.py` - ensure_wal_mode()
- `backend/app/main.py` - CORS write methods + WAL no lifespan
- `backend/tests/test_migrations.py` - Upgrade/downgrade/empty DB tests
- `.env.example` - RUN_MIGRATIONS_ON_STARTUP=false

## Decisions Made

- Migration detecta DB vazio vs v1.0: cria `print_jobs` completo ou usa `batch_alter_table`
- Alembic não roda automaticamente no startup (watcher isolation D-29/D-31)
- env.py usa `os.environ.get("DB_PATH")` para suportar testes e paths dinâmicos

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Migration falhava em DB vazio**
- **Found during:** Task 4
- **Issue:** `batch_alter_table('print_jobs')` falhava quando tabela não existia
- **Fix:** Lógica condicional — create_table em DB vazio, batch_alter em DB v1.0
- **Files modified:** `backend/alembic/versions/085a2d5c5767_master_data_tables.py`
- **Verification:** `test_upgrade_on_empty_db` passa; `alembic upgrade head` em DB vazio OK
- **Committed in:** `2c0f054`

**2. [Rule 2 - Missing Critical] env.py ignorava DB_PATH em testes**
- **Found during:** Task 4
- **Issue:** `settings.db_path` cacheado na importação; testes apontavam para DB errado
- **Fix:** Ler `os.environ.get("DB_PATH", settings.db_path)` em runtime
- **Files modified:** `backend/alembic/env.py`
- **Verification:** `test_downgrade_and_reupgrade` passa
- **Committed in:** `2c0f054`

**3. [Rule 1 - Bug] conftest referenciava models.Base inexistente**
- **Found during:** Task 3
- **Issue:** Cleanup de testes usava `models.Base.metadata` (AttributeError)
- **Fix:** Importar `Base` de `app.db.base` no fixture db_session
- **Files modified:** `backend/tests/conftest.py`
- **Verification:** `pytest -q` — 85 passed
- **Committed in:** `849dd7b`

---

**Total deviations:** 3 auto-fixed (2 bugs, 1 missing critical)
**Impact on plan:** Correções necessárias para migration em DB vazio e suite de testes confiável. Sem scope creep.

## Issues Encountered

None blocking — downgrade/reupgrade validado via pytest.

## User Setup Required

None — aplicar migrations em deploy com:

```bash
cd backend && alembic upgrade head
```

## Verification Results

- `alembic upgrade head` — PASS (DB vazio e v1.0 simulado)
- `pytest -q` — PASS (85 tests)
- `pytest tests/test_migrations.py -q` — PASS (4 tests)
- `alembic current` — `085a2d5c5767 (head)`

## Next Phase Readiness

- Schema foundation pronta para Plan 05-02 (normalize core) e CRUD APIs
- `printer_id` nullable preserva INSERT do watcher sem FK enforcement no hot path
- Matcher pode usar índice `idx_print_jobs_printer_id_null`

## Self-Check: PASSED

- FOUND: backend/alembic/env.py
- FOUND: backend/alembic/versions/085a2d5c5767_master_data_tables.py
- FOUND: backend/tests/test_migrations.py
- FOUND: commit dfbe4fa
- FOUND: commit bba697c
- FOUND: commit 849dd7b
- FOUND: commit 2c0f054

---
*Phase: 05-master-data-organization*
*Completed: 2026-05-27*
