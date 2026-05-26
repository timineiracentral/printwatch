---
phase: 02-log-pipeline-data-layer
plan: "02"
subsystem: capture
tags: [parser, tail-reader, pytest, tdd, page-log, cups]

requires:
  - phase: 02-log-pipeline-data-layer
    plan: "01"
    provides: backend scaffold, pytest in requirements, Settings.log_path
provides:
  - PAGE_LOG_REGEX parser with D-08/D-09/D-15 field mapping
  - TailReader with inode+byte_offset checkpoint and logrotate detection
  - 15 pytest unit tests runnable without Docker
affects: [02-03 watcher integration, phase-3-api]

tech-stack:
  added: []
  patterns:
    - "TDD RED→GREEN: test commit then feat commit"
    - "StubStateRepo protocol for TailReader tests"
    - "Parser returns None for non-matching lines (pitfall 7)"

key-files:
  created:
    - backend/app/services/parser.py
    - backend/app/services/tail_reader.py
    - backend/tests/conftest.py
    - backend/tests/test_parser.py
    - backend/tests/test_tail_reader.py
    - backend/pytest.ini
  modified:
    - backend/app/services/__init__.py

key-decisions:
  - "state_repo.get()/upsert(inode=, byte_offset=) sem path — alinhado ao Plano 03 CheckpointRepository"
  - "REFACTOR omitido: log_path já em Settings; type hints completos no GREEN"

patterns-established:
  - "_null_if_dash: strip + sentinel '-' → None (D-09)"
  - "TailReader: seek no restart mesmo inode; reopen offset 0 se inode mudou"

requirements-completed: [CAPTURE-01, CAPTURE-02, CAPTURE-03]

duration: 12min
completed: 2026-05-26
---

# Phase 2 Plan 02: Parser + TailReader TDD Summary

**Parser PAGE_LOG_REGEX e TailReader com checkpoint inode/offset cobertos por 15 testes pytest locais (sem container)**

## Performance

- **Duration:** 12 min
- **Started:** 2026-05-26T19:00:00Z
- **Completed:** 2026-05-26T19:12:00Z
- **Tasks:** 2 (TDD RED + GREEN)
- **Files modified:** 9

## Accomplishments

- `parse_page_log_line` mapeia 10 grupos do regex, timestamp timezone-aware, status `allowed`, copies `None`
- `_null_if_dash` converte `-` (com espaços) para `None`; username AD mantido sem normalização
- `TailReader` recupera offset no restart (mesmo inode) e reabre do início após logrotate (inode diferente)
- Suite `python -m pytest tests/ -v` — 15 passed, 0 failed

## Task Commits

1. **TDD RED: testes parser + tail_reader** - `09e2828` (test)
2. **TDD GREEN: implementação parser + tail_reader** - `5bff109` (feat)

## TDD Gate Compliance

| Gate | Commit | Status |
|------|--------|--------|
| RED | `09e2828` test(02-02) | ✓ |
| GREEN | `5bff109` feat(02-02) | ✓ |
| REFACTOR | — | N/A (não necessário) |

## Files Created/Modified

- `backend/app/services/parser.py` - PAGE_LOG_REGEX, `_null_if_dash`, `parse_page_log_line`
- `backend/app/services/tail_reader.py` - TailReader com StateRepo protocol
- `backend/tests/test_parser.py` - 10 testes de parse e sentinel
- `backend/tests/test_tail_reader.py` - 5 testes de leitura, restart e inode
- `backend/tests/conftest.py` - fixtures sample line, tmp log, StubStateRepo
- `backend/pytest.ini` - testpaths + pythonpath

## Deviations from Plan

None - plan executed exactly as written. REFACTOR phase skipped intentionally (config.log_path already exists; type hints complete).

## Self-Check

- FOUND: backend/app/services/parser.py
- FOUND: backend/app/services/tail_reader.py
- FOUND: backend/tests/test_parser.py
- FOUND: backend/tests/test_tail_reader.py
- FOUND: backend/pytest.ini
- FOUND: commit 09e2828
- FOUND: commit 5bff109
- **Self-Check: PASSED**
