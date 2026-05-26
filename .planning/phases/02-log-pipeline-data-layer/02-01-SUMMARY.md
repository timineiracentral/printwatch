---
phase: 02-log-pipeline-data-layer
plan: "01"
subsystem: infra
tags: [docker, sqlalchemy, sqlite, fastapi, watchdog, python]

requires:
  - phase: 01-infrastructure-print-server
    provides: cups_logs volume, CUPS page_log, docker-compose base
provides:
  - Backend container image (python:3.11-slim)
  - SQLite schema print_jobs, capture_state, policies
  - docker-compose backend service with db_data volume
  - Settings via env (DB_PATH, LOG_PATH, LOG_RETENTION_DAYS)
affects: [02-log-pipeline-data-layer plans 02-04, phase-3-api]

tech-stack:
  added: [watchdog 6.0.0, sqlalchemy 2.0.50, fastapi 0.136.3, uvicorn 0.48.0, pydantic 2.13.4, pytest 8.3.5]
  patterns: [NullPool SQLite, Mapped/mapped_column, entrypoint exec uvicorn PID 1, chmod 600 DATA-03]

key-files:
  created:
    - backend/Dockerfile
    - backend/entrypoint.sh
    - backend/requirements.txt
    - backend/app/main.py
    - backend/app/core/config.py
    - backend/app/db/base.py
    - backend/app/db/models.py
    - backend/app/db/session.py
  modified:
    - docker-compose.yml
    - .env.example

key-decisions:
  - "Base em arquivo separado (db/base.py) para evitar imports circulares"
  - "create_all na importação de session.py; entrypoint importa session antes do chmod 600"
  - "FastAPI app mínima sem rotas/docs (D-12) — uvicorn apenas como processo principal"

patterns-established:
  - "SQLAlchemy 2.x DeclarativeBase + Mapped/mapped_column em models.py unificado"
  - "SQLite NullPool + check_same_thread=False para uso futuro com watcher em thread"
  - "entrypoint: set -euo pipefail, defaults via env, exec uvicorn"

requirements-completed: [CAPTURE-04, DATA-01, DATA-02, DATA-03, EXTEND-01, EXTEND-02]

duration: 18min
completed: 2026-05-26
---

# Phase 2 Plan 01: Backend Container + SQLite Schema Summary

**Container backend Docker com SQLite persistido (print_jobs, capture_state, policies), permissões 600 e compose integrado ao volume cups_logs:ro**

## Performance

- **Duration:** 18 min
- **Started:** 2026-05-26T18:20:00Z
- **Completed:** 2026-05-26T18:38:00Z
- **Tasks:** 2
- **Files modified:** 14

## Accomplishments

- Imagem `backend` (python:3.11-slim) com watchdog, SQLAlchemy, FastAPI e pytest no requirements
- Schema SQLite com `PrintJob` (status default `allowed`, UNIQUE `uq_page_log_line`), `CaptureState`, `Policy`
- Serviço `backend` no docker-compose com `cups_logs:ro` e volume `db_data`
- Verificação local: `docker compose up -d backend`, tabelas criadas, `stat` mostra `0600`

## Task Commits

1. **Task 1: Infraestrutura Docker do backend** - `a05fdc5` (feat)
2. **Task 2: Modelos SQLAlchemy + engine + docker-compose** - `09f748f` (feat)

## Files Created/Modified

- `backend/Dockerfile` - Imagem Python sem EXPOSE (D-12)
- `backend/entrypoint.sh` - Pre-init DB, chmod 600, exec uvicorn
- `backend/requirements.txt` - Pin de dependências Fase 2 + pytest
- `backend/app/db/models.py` - Três modelos ORM 2.x
- `backend/app/db/session.py` - Engine NullPool, create_all, get_db
- `backend/app/core/config.py` - Settings via os.environ
- `backend/app/main.py` - FastAPI vazio (sem rotas públicas)
- `docker-compose.yml` - Serviço backend + volume db_data
- `.env.example` - DB_PATH, LOG_PATH, LOG_RETENTION_DAYS

## Decisions Made

- `session.py` importa `models` antes de `create_all` para registrar metadata
- Entrypoint executa `python -c "import app.db.session"` antes do chmod para cobrir DB criado no primeiro boot

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] chmod 600 após criação do SQLite no primeiro boot**
- **Found during:** Task 2 (verificação `stat` do banco)
- **Issue:** `create_all` roda na importação do uvicorn, depois do bloco `chmod` do entrypoint original — DB novo ficava sem 600
- **Fix:** Entrypoint importa `app.db.session` antes do `chmod 600`, depois `exec uvicorn`
- **Files modified:** `backend/entrypoint.sh`
- **Verification:** `docker compose exec backend stat /app/data/printwatch.db` → `Access: (0600/-rw-------)`
- **Committed in:** `09f748f`

**2. [Rule 2 - Missing Critical] `app/main.py` mínimo para uvicorn**
- **Found during:** Task 1 (docker build COPY app/ + entrypoint `app.main:app`)
- **Issue:** Plano referencia uvicorn mas não listava main.py na Task 2; build e runtime exigem o módulo
- **Fix:** FastAPI app sem rotas/docs (`docs_url=None`)
- **Files modified:** `backend/app/main.py`
- **Committed in:** `09f748f`

---

**Total deviations:** 2 auto-fixed (2 missing critical)
**Impact on plan:** Necessários para DATA-03 e container funcional; sem expansão de escopo.

## Issues Encountered

- PowerShell não aceita `&&` em scripts — usado `Set-Location` + comandos separados

## User Setup Required

None - variáveis documentadas em `.env.example`; copiar para `.env` se ainda não existir.

## Next Phase Readiness

- Pronto para Plano 02 (parser + testes) e Plano 03 (watcher/tail)
- `SessionLocal`, modelos e volume `db_data` disponíveis
- `LOG_RETENTION_DAYS` em config — purge ainda não implementado (planos posteriores)

## Self-Check: PASSED

- FOUND: backend/Dockerfile
- FOUND: backend/app/db/models.py
- FOUND: backend/app/db/session.py
- FOUND: docker-compose.yml (backend + db_data)
- FOUND: .planning/phases/02-log-pipeline-data-layer/02-01-SUMMARY.md
- FOUND: commit a05fdc5
- FOUND: commit 09f748f

---
*Phase: 02-log-pipeline-data-layer*
*Completed: 2026-05-26*
