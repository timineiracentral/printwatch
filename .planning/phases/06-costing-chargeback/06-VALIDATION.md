---
phase: 6
slug: costing-chargeback
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-27
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | `backend/tests/conftest.py` |
| **Quick run command** | `cd backend && pytest -q tests/test_cost_rates.py tests/test_cost_service.py tests/test_chargeback_export.py` |
| **Full suite command** | `cd backend && pytest -q` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick run command
- **After every plan wave:** Run full suite command
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | COST-01 | T-06-01 | Migration reversível | unit | `cd backend && alembic upgrade head` | ⬜ W0 | ⬜ pending |
| 06-01-02 | 01 | 1 | COST-02 | T-06-02 | Watcher sem import cost | unit | `grep -r cost_rates backend/app/watcher` empty | ⬜ W0 | ⬜ pending |
| 06-02-01 | 02 | 2 | COST-01,02 | T-06-03 | rate_at usa valid_from | unit | `pytest -q tests/test_cost_service.py` | ⬜ W0 | ⬜ pending |
| 06-02-02 | 02 | 2 | COST-01 | — | POST nova vigência não apaga histórico | unit | `pytest -q tests/test_cost_rates.py` | ⬜ W0 | ⬜ pending |
| 06-03-01 | 03 | 3 | COST-03 | — | JobOut estimated_cost quando rates existem | unit | `pytest -q tests/test_jobs_cost.py` | ⬜ W0 | ⬜ pending |
| 06-03-02 | 03 | 3 | COST-02 | — | PATCH manual torna linha faturável | unit | `pytest -q tests/test_jobs_color_patch.py` | ⬜ W0 | ⬜ pending |
| 06-04-01 | 04 | 3 | CHRG-01..03 | T-06-04 | outside_policy excluído CSV | unit | `pytest -q tests/test_chargeback_export.py` | ⬜ W0 | ⬜ pending |
| 06-05-01 | 05 | 4 | COST-03 | — | UI coluna custo opcional | manual | Jobs page toggle | — | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_cost_service.py` — rate_at, billable line cost
- [ ] `backend/tests/test_cost_rates.py` — API CRUD/histórico
- [ ] `backend/tests/test_chargeback_export.py` — buckets + exclusion
- [ ] `backend/tests/test_jobs_color_patch.py` — PATCH manual

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CUPS color no page_log | COST-02 / D-05 | Requer fila real | Rodar `fix-cups-color-queue.sh`; imprimir testpage; verificar campo 6 no log |
| Settings Tarifas UX | COST-01 | Visual | Criar vigência; confirmar histórico e R$ formatado |

---
