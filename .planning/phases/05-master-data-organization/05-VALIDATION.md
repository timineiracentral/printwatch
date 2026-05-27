---
phase: 5
slug: master-data-organization
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-05-27
---

# Phase 5 — Validation Strategy

> Contrato de validação para execução da Fase 5 (Master Data & Organization).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (backend) |
| **Config file** | `backend/pyproject.toml` |
| **Quick run command** | `cd backend && pytest -q --tb=no` |
| **Full suite command** | `cd backend && pytest` |
| **Frontend smoke** | `cd frontend && npm run build` |
| **Estimated runtime** | ~30–90 seconds (backend full) |

---

## Sampling Rate

- **After every task commit:** `cd backend && pytest -q --tb=no`
- **After every plan wave:** `cd backend && pytest` + `cd frontend && npm run build`
- **Before `/gsd-verify-work`:** Full suite green + manual P5-AC-04 se possível
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | Status |
|---------|------|------|-------------|-----------|-------------------|--------|
| 05-01-01 | 01 | 1 | DATA-04, DATA-05 | integration | `pytest tests/test_migrations.py -q` | ⬜ pending |
| 05-01-02 | 01 | 1 | DATA-06, DATA-07 | unit | `pytest -q` (WAL + is_active columns) | ⬜ pending |
| 05-02-01 | 02 | 2 | D-05 | unit | `pytest tests/test_normalization.py -q` | ⬜ pending |
| 05-03-01 | 03 | 2 | INV-01–03, INV-06 | unit | `pytest tests/test_printers_api.py -q` | ⬜ pending |
| 05-04-01 | 04 | 2 | ORG-01–09 | unit | `pytest tests/test_org_api.py -q` | ⬜ pending |
| 05-05-01 | 05 | 3 | INV-04, INV-05 | unit | `pytest tests/test_matcher.py -q` | ⬜ pending |
| 05-06-01 | 06 | 3 | IMPORT-01–05 | unit | `pytest tests/test_import_csv.py -q` | ⬜ pending |
| 05-07-01 | 07 | 4 | SETTINGS-01–04, SERVER-04 | build | `cd frontend && npm run build` | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_migrations.py` — alembic upgrade/downgrade em DB temp
- [ ] `backend/tests/test_matcher.py` — batch limitado, só NULL printer_id
- [ ] `backend/tests/test_import_csv.py` — partial vs strict
- [ ] `backend/tests/test_printers_api.py` — CRUD + unmapped-queues

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Backend down, print succeeds | P5-AC-04, SETTINGS-03 | Docker lifecycle | `docker compose stop backend`; imprimir; verificar job no SQLite |
| Backfill ≥95% histórico | P5-AC-02 | Volume real | Registrar printers; POST backfill; SQL count |
| printer_id em 5 min | P5-AC-01 | Tempo | Novo job; aguardar matcher 60s |

---

## Blocking Commands

| Step | Command | When |
|------|---------|------|
| Schema push | `cd backend && alembic upgrade head` | Após plan 05-01 migrations committed |

---

*Validation strategy — Phase 5 — 2026-05-27*
