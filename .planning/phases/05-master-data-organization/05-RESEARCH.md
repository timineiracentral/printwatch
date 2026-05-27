# Phase 5 — Technical Research

**Researched:** 2026-05-27  
**Phase:** Master Data & Organization  
**Status:** RESEARCH COMPLETE

---

## Summary

Fase 5 adiciona cadastro mestre (printers, departments, cost_centers, users), import CSV e vínculo assíncrono `printer_id` em `print_jobs`, **sem tocar o hot path do watcher**. O codebase v1.0 já tem `normalize_printer_name` em `backend/app/services/normalization.py`, FastAPI com lifespan/inotify, e frontend AppShell + design tokens da Fase 4. As decisões D-01–D-31 em `05-CONTEXT.md` fecham arquitetura; esta pesquisa detalha **como implementar** com Alembic, SQLAlchemy 2.0, FastAPI e React Router.

**Documentação consultada (Context7):** Alembic batch mode SQLite, FastAPI BackgroundTasks/UploadFile, lifespan patterns.

---

## Standard Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Migrations | **Alembic** | D-19; reversível; `batch_alter_table` obrigatório no SQLite para ALTER |
| ORM | SQLAlchemy 2.0 `Mapped` | Já usado em `models.py` |
| API | FastAPI 0.136 | Routers v1 existentes; estender CORS para POST/PATCH |
| Matcher | `asyncio` task no lifespan + `BackgroundTasks` on-save | D-02, D-03; não bloquear requests |
| CSV | `csv.DictReader` + Pydantic row schemas | Sem pandas — dependência leve |
| Frontend routing | **react-router-dom** (adicionar) | D-08 `/settings/*` sem SPA monolítica |
| State | TanStack Query | Padrão Fase 4 (`usePrinters`) |

---

## Architecture

```
Watcher (INSERT print_jobs, printer string only)
        ↓
SQLite print_jobs.printer_id NULL
        ↓
Matcher (60s batch) + on-save printer hook + POST /admin/backfill-printer-ids
        ↓
printers.cups_queue_name ←normalize→ print_jobs.printer

Settings UI ──CRUD──► /api/v1/{entity}
Import CSV ──POST──► /api/v1/import/{entity}
Audit /jobs ──unchanged capture path──► DISTINCT migrado para registry em FilterBar
```

### Watcher isolation (critical)

- `PageLogHandler` / `PrintJobRepository` **não** importam `Printer`, `Department`, etc.
- Permitido: `from app.core.normalize import normalize_printer_name` (mover de `services/normalization.py` — D-05)
- `printer_id` preenchido apenas por matcher/backfill/on-save — nunca no INSERT do watcher

---

## Alembic + SQLite

**Fonte:** [Alembic batch operations](https://alembic.sqlalchemy.org/en/latest/batch.html) via Context7.

- Inicializar em `backend/alembic/` com `target_metadata = Base.metadata` de `app.db.base`
- `env.py`: usar engine síncrono `sqlite:///{DATABASE_URL}` — projeto já usa Session síncrona
- **Toda** alteração em tabela existente (`print_jobs`) deve usar `op.batch_alter_table('print_jobs')` no SQLite
- Comando deploy: `alembic upgrade head` — **[BLOCKING]** após migrations commitadas
- Downgrade: testar `alembic downgrade -1` em dev antes de merge

**WAL (DATA-06):** `PRAGMA journal_mode=WAL` no startup se ainda não aplicado — verificar `session.py`/lifespan.

**Índice matcher (D-21):** `CREATE INDEX IF NOT EXISTS idx_print_jobs_printer_id_null ON print_jobs(printer) WHERE printer_id IS NULL` — partial index SQLite; ou composto `(printer_id, printer)` conforme EXPLAIN.

---

## Schema (implementation)

### New tables

```text
printers(id, display_name, cups_queue_name UNIQUE, ip_address, manufacturer_model,
         location, department_id FK nullable, is_active, created_at, updated_at)

departments(id, code UNIQUE, name, cost_center_id FK nullable, is_active, ...)

cost_centers(id, code UNIQUE, name, is_active, ...)

users(id, cups_username UNIQUE, display_name, department_id FK, cost_center_id FK nullable, is_active, ...)
```

### print_jobs alteration

- `printer_id INTEGER REFERENCES printers(id)` — **nullable**, sem `ON DELETE` restrict no INSERT path
- Manter coluna `printer` (string) — fonte do log; matcher preenche FK

### Code normalization (D-16)

- `departments.code`, `cost_centers.code`: strip → upper → validate uniqueness case-insensitive via `func.upper(code)`
- Persist UPPERCASE

---

## API Design

### CORS breaking change

`main.py` hoje: `allow_methods=["GET"]`. Fase 5 exige `GET, POST, PATCH, PUT, DELETE` (ou `["*"]` restrito a origens explícitas).

### Printers registry vs legacy endpoint

- **Substituir** semântica de `GET /api/v1/printers` (DISTINCT strings) por lista de objetos registry **ou** manter path e mudar response model com version bump documentado
- **Decisão de plano:** `GET /api/v1/printers` retorna `list[PrinterRead]` do registry; audit FilterBar migra no plan 07
- `GET /api/v1/printers/unmapped-queues` → `SELECT DISTINCT printer FROM print_jobs WHERE printer NOT IN (SELECT normalized cups_queue_name FROM printers)` usando mesma normalize

### CRUD patterns

Reutilizar estrutura de `jobs.py`: router + service + Pydantic schemas + `Depends(get_db_dep)`.

Soft delete: PATCH com `is_active=false`; list endpoints filtram `?include_inactive=true` para admin.

### Import (D-23–24)

```text
POST /api/v1/import/{entity}?strict=false
Content-Type: multipart/form-data
file: UploadFile

Response: { total, created, updated, skipped, errors: [{ line, message }] }
```

**Fonte:** FastAPI `UploadFile` + `File()` — Context7.

- `strict=true`: transação única; qualquer erro → rollback total
- Default: commit por linha válida em sub-transactions ou savepoint per row

### Matcher service

```python
# Pseudologic
def match_batch(session, *, limit=500):
    rows = session.execute(
        select(PrintJob.id, PrintJob.printer)
        .where(PrintJob.printer_id.is_(None))
        .limit(limit)
    )
    for job_id, printer_name in rows:
        pid = resolve_printer_id(session, printer_name)
        if pid:
            session.execute(update(PrintJob).where(PrintJob.id == job_id).values(printer_id=pid))
```

- Interval: 60s via `asyncio.create_task` loop no lifespan (cancel no shutdown)
- On-save: após `POST/PATCH /printers`, chamar `match_jobs_for_queue(session, cups_queue_name)` síncrono em BackgroundTasks

### Backfill admin

`POST /api/v1/admin/backfill-printer-ids` → loop batches até 0 updates ou max iterations; retorna `{ matched, remaining_null }`.

---

## Frontend

### react-router-dom

- `BrowserRouter` em `main.tsx`
- Routes: `/` → JobsPage (extrair de App.tsx), `/settings/*` → SettingsLayout
- Sidebar: `NavLink` com `aria-current`

### API client

- Estender `frontend/src/api/client.ts` para POST/PATCH/multipart
- Tipos em `types/api.ts` para entidades mestre

---

## Pitfalls (from PITFALLS.md)

| Risk | Mitigation |
|------|------------|
| Watcher imports org models | Lint/import guard; code review task |
| SQLite lock on backfill | Batch 500, WAL, off-peak manual trigger |
| Queue name drift | Single `normalize_printer_name` in `app.core.normalize` |
| CORS blocks CRUD | Plan 01 explicit CORS update |

---

## Validation Architecture

### Test infrastructure

| Property | Value |
|----------|-------|
| Backend framework | pytest |
| Backend quick | `cd backend && pytest -q --tb=no` |
| Backend full | `cd backend && pytest` |
| Frontend | vitest (se existir) ou `npm run build` como smoke |
| Config | `backend/pyproject.toml` / `pytest.ini` |

### Wave 0

- `backend/tests/test_migrations.py` — upgrade head em SQLite temp file
- `backend/tests/test_matcher.py` — unit com fixtures printers + jobs
- `backend/tests/test_import_csv.py` — partial vs strict
- `backend/tests/test_printers_crud.py`

### Manual-only

| Behavior | Why |
|----------|-----|
| P5-AC-04 watcher independente com backend down | Requer docker stop backend + print real |
| ≥95% backfill em volume produção | Dataset dependente |

### Per-phase automated focus

- Normalização idempotente (reuso testes Fase 3)
- Matcher só atualiza `printer_id IS NULL`
- Import 48/50 linhas em strict=false
- CRUD soft-delete não remove histórico

---

## Sources

- Context7 `/websites/alembic_sqlalchemy` — batch_alter_table, SQLite migrations
- Context7 `/fastapi/fastapi` — BackgroundTasks, UploadFile
- `.planning/phases/05-master-data-organization/05-CONTEXT.md`
- `.planning/research/PITFALLS.md`
- `backend/app/main.py`, `backend/app/db/models.py`

---

## RESEARCH COMPLETE

**Phase directory:** `.planning/phases/05-master-data-organization/`  
**Ready for:** `/gsd-plan-phase 5` planner
