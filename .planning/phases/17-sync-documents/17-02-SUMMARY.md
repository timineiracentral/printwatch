---
phase: 17-sync-documents
plan: 02
subsystem: testing
tags: [pytest, simpress, sync, tdd, nyquist]

requires:
  - phase: 17-01
    provides: Invoice/SyncRun models, sync schemas, SimpressSettings docs_path/public_base_url
provides:
  - FakePortal determinístico em conftest_simpress (sem Playwright/rede)
  - Suites RED para sync_service, daily_sync_loop, document_store, public_docs, sync API
  - Extensão ISO-01 com sync fake e paths temporários
affects: [17-03, 17-04, 17-05, 17-06, 17-09]

tech-stack:
  added: []
  patterns:
    - "importlib + pytest.fail para módulos ainda ausentes (coleta OK, execução RED)"
    - "FakePortal com shape do spike 001 e bytes ZIP PK"

key-files:
  created:
    - backend/tests/test_simpress_sync_service.py
    - backend/tests/test_simpress_daily_sync_loop.py
    - backend/tests/test_simpress_document_store.py
    - backend/tests/test_simpress_public_docs.py
    - backend/tests/test_simpress_sync_api.py
  modified:
    - backend/tests/conftest_simpress.py
    - backend/tests/test_simpress_isolation.py

key-decisions:
  - "Fixtures definem SIMPRESS_DOCS_PATH e PUBLIC_BASE_URL antes do reload do app"
  - "Testes de serviço importam sync_service/invoices_service/document_store sob demanda"

patterns-established:
  - "FakePortal registra contracts_called, list_calls e download_calls para asserts ACL/filtro/D-04"

requirements-completed: [SYNC-01, SYNC-02, SYNC-03, SYNC-04]

duration: 25min
completed: 2026-08-05
---

# Phase 17 Plan 02 Summary

**Rede Nyquist de testes para sync, storage ZIP e API — contratos D-01..D-14 e ISO-01 antes da implementação.**

## Performance

- **Duration:** ~25 min
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments

- `FakePortal` assíncrono com contratos ACL, paginação, filtro por CNPJ e download ZIP `PK`
- 12 testes de orquestração cobrindo D-03, D-04, D-05, D-06, D-08, D-09 e sanitização de erros
- 4 casos explícitos de `should_run_daily` (D-02) em `America/Sao_Paulo`
- Lifecycle token/ZIP, traversal `..`/slash/backslash e rota pública `application/zip`
- API sync: 202, 409 `sync em andamento`, status, last summary sem segredos
- Isolamento: `print_jobs` inalterado após sync fake; DB/ZIP em paths temporários

## Task Commits

1. **Task 1: Criar fixture de portal e testes do orquestrador** - `67e6ee4`
2. **Task 2: Especificar storage e rota ZIP pública segura** - `96d9695`
3. **Task 3: Especificar API single-flight, diagnóstico e isolamento** - `89146e9`

**Plan metadata:** ver commit `docs(17-02)` abaixo

## Verificação RED

| Comando | Resultado |
|---------|-----------|
| `pytest tests/test_simpress_sync_service.py tests/test_simpress_daily_sync_loop.py -q` | 16 failed (coleta OK) |
| `pytest tests/test_simpress_document_store.py tests/test_simpress_public_docs.py -q` | 6 failed, 4 passed (traversal 404 antecipado) |
| `pytest tests/test_simpress_sync_api.py tests/test_simpress_isolation.py -q` | 5 failed, 4 passed |

Falhas esperadas: módulos `sync_service`, `document_store`, `daily_sync_loop` e rotas `/sync`/`/public/docs` ainda ausentes.

## Deviations from Plan

Nenhuma — plano executado conforme escrito. Tasks 2 e 3 foram recomitadas separadamente após colisão de `index.lock`.

## Next Phase Readiness

- Planos 17-03..17-06 podem implementar serviços/rotas guiados pelos testes RED
- Mesmos comandos pytest devem ficar verdes após ondas 3–5

## Self-Check: PASSED

- [x] Fixtures `fake_portal`, `simpress_docs_path`, `PUBLIC_BASE_URL` em conftest
- [x] Asserts separados D-03, D-04, D-05, D-06, D-08, D-09
- [x] Quatro casos D-02 em `test_simpress_daily_sync_loop.py`
- [x] Traversal e ZIP-only (zero `.pdf`) cobertos
- [x] API 202/409/status/last e ISO-01 print_jobs
- [x] Três suítes pytest coletam e retornam exit code != 0
- [x] Nenhuma implementação de sync_service/document_store/rotas neste plano

---
*Phase: 17-sync-documents*
*Completed: 2026-08-05*
