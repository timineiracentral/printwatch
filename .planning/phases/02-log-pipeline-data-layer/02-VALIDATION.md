---
phase: 02
slug: log-pipeline-data-layer
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-26
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (instalado no Wave 0 via `requirements.txt`) |
| **Config file** | `backend/pytest.ini` (criar no Wave 0) |
| **Quick run command** | `cd backend && pytest tests/ -x -q` |
| **Full suite command** | `cd backend && pytest tests/ -v && bash scripts/validate-phase2.sh --quick` |
| **Estimated runtime** | ~30 segundos (testes unit) + ~60s (validate-phase2.sh --quick) |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && pytest tests/ -x -q`
- **After every plan wave:** Run `cd backend && pytest tests/ -v && bash scripts/validate-phase2.sh --quick`
- **Before `/gsd-verify-work`:** Full suite must be green + checkpoint humano aprovado
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | DATA-02, DATA-03, CAPTURE-04, EXTEND-01, EXTEND-02 | T-02-01/T-02-02 | SQLite permissões 600; volume db_data não exposto na rede | unit + smoke | `docker compose build backend --no-cache` exits 0 | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | EXTEND-01, EXTEND-02, DATA-03 | T-02-03 | status default `allowed`; tabela policies vazia; chmod 600 aplicado | unit | `pytest tests/test_models.py -x -q` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 1 | CAPTURE-01, DATA-01 | T-02-04/T-02-05 | NULL para campos ausentes (`-`); username preservado sem strip | unit (TDD) | `pytest tests/test_parser.py tests/test_tail_reader.py -x -q` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 2 | CAPTURE-01, CAPTURE-02, CAPTURE-03, CAPTURE-04, EXTEND-03 | T-02-06/T-02-07 | INSERT idempotente; hook retorna True; volume :ro | unit + integration | `pytest tests/test_repository.py tests/test_service.py -x -q` | ❌ W0 | ⬜ pending |
| 02-03-02 | 03 | 2 | — (healthcheck interno D-13) | T-02-08 | /healthz não é rota pública (D-12 exceção consciente via D-13) | smoke | `docker compose exec backend curl -sf http://localhost:8000/healthz` | ❌ W0 | ⬜ pending |
| 02-04-01 | 04 | 3 | DATA-01 | T-02-09 | purge usa timezone-aware; não deleta registros dentro da janela | unit (TDD) | `pytest tests/test_retention.py -x -q` | ❌ W0 | ⬜ pending |
| 02-04-02 | 04 | 3 | DATA-01, DATA-02 | T-02-10 | LOG_RETENTION_DAYS controla período; registros preservados após restart | smoke | `docker compose restart backend && docker compose logs backend \| grep -i purge` | ❌ W0 | ⬜ pending |
| 02-05-01 | 05 | 4 | CAPTURE-01–04, DATA-01–03, EXTEND-01–03 | T-02-11/T-02-12 | Script não expõe dados além do terminal admin; CUPS reinicia após teste | smoke | `bash scripts/validate-phase2.sh --quick` exits 0 | ❌ W0 | ⬜ pending |
| 02-05-02 | 05 | 4 | CAPTURE-01, CAPTURE-02 | — | Job Windows com DOMINIO\usuario aparece em ≤ 30s | manual | Ver `<task type="checkpoint:human-verify">` no 02-05-PLAN.md | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/__init__.py` — pacote de testes
- [ ] `backend/tests/conftest.py` — fixtures: engine SQLite in-memory, sessão, sample line do page_log
- [ ] `backend/tests/test_parser.py` — cobre CAPTURE-01, D-08 (username as-is), D-09 (NULL para `-`)
- [ ] `backend/tests/test_tail_reader.py` — cobre CAPTURE-03 (seek no mesmo inode + reprocesso em inode diferente)
- [ ] `backend/tests/test_repository.py` — cobre INSERT idempotente (UNIQUE ON CONFLICT DO NOTHING)
- [ ] `backend/tests/test_models.py` — cobre EXTEND-01 (status default `allowed`), EXTEND-02 (tabela policies)
- [ ] `backend/tests/test_service.py` — cobre EXTEND-03 (pre_process_job retorna True)
- [ ] `backend/tests/test_retention.py` — cobre DATA-01 (purge_old_jobs deleta antigos, preserva recentes)
- [ ] `backend/pytest.ini` — `[pytest]` com `testpaths = tests`
- [ ] `pytest` e `pytest-cov` em `backend/requirements.txt`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Job de PC Windows com `DOMINIO\usuario` aparece no banco em ≤ 30s | CAPTURE-01, CAPTURE-02 | Requer PC Windows real com usuário AD na rede REDACTED_IP/16 | Ver Task 2 do Plano 05 (`<task type="checkpoint:human-verify">`) |
| CUPS imprime fisicamente com container backend parado | CAPTURE-04 | Requer impressora física HP/Samsung conectada | `docker compose stop backend` → imprimir do Windows → confirmar impressão física → `docker compose start backend` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
