---
phase: 02-log-pipeline-data-layer
plan: "03"
subsystem: capture
tags: [watchdog, inotify, fastapi, sqlalchemy, sqlite, repository, pipeline]

requires:
  - phase: 02-log-pipeline-data-layer
    plan: "01"
    provides: PrintJob/CaptureState models, SessionLocal, docker-compose backend
  - phase: 02-log-pipeline-data-layer
    plan: "02"
    provides: parse_page_log_line, TailReader with StateRepo protocol
provides:
  - PrintJobRepository INSERT idempotente (ON CONFLICT DO NOTHING)
  - CheckpointRepository para TailReader
  - PageLogHandler + InotifyObserver no lifespan FastAPI
  - GET /healthz com watcher alive
affects: [02-04 retention, 02-05 validate-phase2, phase-3-api]

tech-stack:
  added: []
  patterns:
    - "sqlite_insert().on_conflict_do_nothing(index_elements=[printer, job_id, timestamp, pages])"
    - "InotifyObserver agenda /var/log/cups/ (dir); handler filtra PAGE_LOG_PATH"
    - "observer.daemon=True + lifespan stop/join"

key-files:
  created:
    - backend/app/db/repository.py
    - backend/app/watcher/checkpoint.py
    - backend/app/watcher/handler.py
    - backend/app/watcher/__init__.py
    - backend/tests/test_repository.py
  modified:
    - backend/app/main.py

key-decisions:
  - "StaticPool em testes :memory: — NullPool abre DB vazio por conexão (desvio Rule 1)"
  - "/healthz exceção consciente a D-12 para probe interno (D-13)"

patterns-established:
  - "pre_process_job() módulo-level retorna True no MVP (EXTEND-03)"
  - "PageLogHandler: session por linha parseada com insert_job_idempotent"

requirements-completed: [CAPTURE-01, CAPTURE-02, CAPTURE-03, CAPTURE-04, DATA-03, EXTEND-03]

duration: 22min
completed: 2026-05-26
---

# Phase 2 Plan 03: Pipeline end-to-end Summary

**Inotify watcher no lifespan FastAPI persiste jobs do page_log no SQLite com INSERT idempotente e checkpoint inode/offset**

## Performance

- **Duration:** 22 min
- **Started:** 2026-05-26T20:00:00Z
- **Completed:** 2026-05-26T20:22:00Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- `PrintJobRepository` com `on_conflict_do_nothing` na unique `uq_page_log_line`
- `CheckpointRepository` implementa `StateRepo` para `TailReader`
- Pipeline: `on_modified` → `read_new_lines` → `parse_page_log_line` → `pre_process_job` → INSERT
- `/healthz` retorna `{"status":"ok","watcher":true}` no container Linux
- 20 testes pytest passando (5 novos em `test_repository.py`)

## Task Commits

1. **Task 1 (RED):** `afedb64` — test(02-03): add failing tests for PrintJobRepository
2. **Task 1 (GREEN):** `099ee58` — feat(02-03): PrintJobRepository idempotent INSERT + CheckpointRepository
3. **Task 2:** `7aebb38` — feat(02-03): PageLogHandler + FastAPI lifespan inotify watcher

## Files Created/Modified

- `backend/app/db/repository.py` — CRUD idempotente + capture_state upsert
- `backend/app/watcher/checkpoint.py` — wrapper SessionLocal para TailReader
- `backend/app/watcher/handler.py` — FileSystemEventHandler filtrado por page_log
- `backend/app/main.py` — lifespan InotifyObserver + /healthz
- `backend/tests/test_repository.py` — 5 testes SQLite in-memory

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] StaticPool nos testes in-memory**
- **Found during:** Task 1 verify
- **Issue:** `NullPool` + `sqlite:///:memory:` cria banco vazio por conexão → "no such table"
- **Fix:** `StaticPool` na fixture `engine_in_memory`
- **Files modified:** `backend/tests/test_repository.py`
- **Commit:** `099ee58`

## Verification Evidence

- `pytest tests/ -v` — 20 passed (local)
- `docker compose exec backend python -c "urllib.../healthz"` — `watcher: true`
- `PrintJob.count()` — 1 no container após startup (page_log existente reprocessado idempotentemente)

## Self-Check: PASSED

- FOUND: backend/app/db/repository.py
- FOUND: backend/app/watcher/handler.py
- FOUND: backend/app/watcher/checkpoint.py
- FOUND: backend/tests/test_repository.py
- FOUND: commit afedb64
- FOUND: commit 099ee58
- FOUND: commit 7aebb38
