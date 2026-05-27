---
phase: 05-master-data-organization
verified: 2026-05-27T18:00:00Z
status: human_needed
score: 6/6
overrides_applied: 0
human_verification:
  - test: "Abrir `/` e usar SummaryCards, FilterBar (PrinterCombobox), JobsTable e paginação após navegar para Settings e voltar"
    expected: "Dashboard de jobs carrega, filtra por impressora do registry e exporta CSV sem regressão"
    why_human: "Comportamento integrado no browser (react-query, rotas) não verificável só por estrutura de componentes"
  - test: "Em `/settings/printers`, `/settings/departments`, `/settings/cost-centers` e `/settings/users`, criar/editar/desativar um registro de cada tipo"
    expected: "Dialogs modais persistem via API; soft-delete reflete `is_active=false`; busca local funciona"
    why_human: "CRUD UI completo exige fluxo real e feedback de erro 409/422"
  - test: "Em `/settings/import`, baixar template, enviar CSV com linhas válidas e inválidas (strict off e on)"
    expected: "Download attachment; painel mostra total/created/updated/skipped/errors; strict=true não persiste linhas com erro"
    why_human: "Upload multipart e renderização do painel de resultado"
  - test: "Cadastrar impressora com fila já presente no log; aguardar ≤5 min ou acionar backfill"
    expected: "Jobs órfãos recebem `printer_id`; banner unmapped diminui"
    why_human: "Critério P5-AC-01/02 depende de dados reais e tempo do matcher 60s"
---

# Phase 5: Master Data & Organization — Verification Report

**Phase Goal:** Admin CRUD for printers, departments, cost centers, users; CSV import; printer_id on jobs via matcher and backfill; watcher unchanged; audit dashboard intact.

**Verified:** 2026-05-27T18:00:00Z  
**Status:** human_needed  
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Admin CRUD completo para printers, departments, cost-centers, users via Settings UI | ✓ VERIFIED | Rotas em `frontend/src/routes/index.tsx`; páginas `PrintersPage`, `DepartmentsPage`, `CostCentersPage`, `UsersPage` com Dialog + ConfirmDialog + hooks API; Sidebar com 5 links em Configurações |
| 2 | CSV import com validação por linha e templates downloadáveis | ✓ VERIFIED | `backend/app/api/v1/import_routes.py`; `import_service.py` (strict/partial, MAX 5MB); 4 templates em `backend/app/import_templates/`; `ImportPage.tsx` com download + upload; `pytest tests/test_import_csv.py` passa |
| 3 | `printer_id` em jobs novos (matcher) e backfill histórico | ✓ VERIFIED | `printer_matcher.py` + loop 60s em `main.py`; on-save via `BackgroundTasks` em `printers.py`; `POST /api/v1/admin/backfill-printer-ids`; `test_matcher.py` + `test_admin_backfill.py` (46 testes fase 5 verdes) |
| 4 | Watcher e impressão física inalterados quando settings/matcher falham | ✓ VERIFIED | `handler.py` só `insert_job_idempotent` sem `printer_id`; sem import de `printer_matcher` em `app.watcher.*`; exceções do matcher isoladas em `_matcher_loop`; CUPS em container separado (`docker-compose.yml`) |
| 5 | Audit dashboard (jobs) funcional com nova navegação Settings | ✓ VERIFIED | `JobsPage` preserva SummaryCards, FilterBar, JobsTable, JobsPagination; rota `/` intacta; `PrinterCombobox` usa `fetchPrintersRegistry` via `api/printers.ts` |
| 6 | CC e Department como entidades independentes | ✓ VERIFIED | Tabelas/modelos separados; routers `/cost-centers` e `/departments`; dept com `cost_center_id` opcional; páginas Settings distintas |

**Score:** 6/6 truths verified (automated)

### Plan-Level Must-Haves (amostra crítica)

| Área | Status | Evidence |
|------|--------|----------|
| Alembic + schema mestre + WAL | ✓ VERIFIED | `backend/alembic/versions/085a2d5c5767_master_data_tables.py`; `ensure_wal_mode` em `db/migrations.py`; `test_migrations.py` |
| `normalize` centralizado (D-05) | ✓ VERIFIED | `app/core/normalize.py`; parser/import/matcher/services usam o mesmo módulo |
| Registry + unmapped-queues | ✓ VERIFIED | `printers_service.list_unmapped_queues`; `GET /printers/unmapped-queues`; `UnmappedQueuesBanner` |
| Org CRUD + soft-delete | ✓ VERIFIED | `departments.py`, `cost_centers.py`, `users.py` + services; `test_org_api.py` |
| Matcher desacoplado do watcher | ✓ VERIFIED | `grep printer_matcher backend/app/watcher` → vazio |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/alembic/versions/085a2d5c5767_master_data_tables.py` | Schema mestre + printer_id | ✓ VERIFIED | 4 tabelas mestre; batch_alter print_jobs; índice parcial `idx_print_jobs_printer_id_null` |
| `backend/app/db/models.py` | Printer, Department, CostCenter, User | ✓ VERIFIED | `is_active`, timestamps, FK printer_id nullable |
| `backend/app/services/printer_matcher.py` | Matcher batch/on-save | ✓ VERIFIED | 86 linhas; sem dependência do watcher |
| `backend/app/api/v1/printers.py` | CRUD + unmapped | ✓ VERIFIED | Wired em `api_v1_router` |
| `backend/app/api/v1/import_routes.py` | Import + templates | ✓ VERIFIED | 4 entidades enum |
| `frontend/src/routes/index.tsx` | /settings/* + / | ✓ VERIFIED | react-router-dom ^6.30 |
| `frontend/src/pages/settings/*.tsx` | CRUD UI 4 entidades + import | ✓ VERIFIED | Dialog/modal pattern em todas |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `PrintersPage` | `POST/PATCH /api/v1/printers` | `usePrintersRegistry` hooks | ✓ WIRED | create/update/deactivate + invalidate queries |
| `create_printer_endpoint` | `match_jobs_for_queue` | `BackgroundTasks` + `matcher_hooks` | ✓ WIRED | `printers.py` L29-30, L57-58 |
| `main.py lifespan` | `match_batch` | `_matcher_loop` 60s | ✓ WIRED | L30-42, task criada L84 |
| `PageLogHandler` | `PrintJob` INSERT | `insert_job_idempotent` | ✓ WIRED | Sem `printer_id` no dict |
| `PrinterCombobox` | `/api/v1/printers` | `fetchPrintersRegistry` | ✓ WIRED | Registry canônico, não DISTINCT legado |
| `ImportPage` | `/api/v1/import/*` | `useImportCsv` | ✓ WIRED | template download + multipart POST |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `PrinterCombobox` | `printers` | `useQuery` → `GET /printers` | API DB registry | ✓ FLOWING |
| `PrintersPage` unmapped banner | `unmapped.data` | `GET /printers/unmapped-queues` | DISTINCT jobs vs registry | ✓ FLOWING |
| `JobsTable` | jobs list | jobs API (fase 4) | Não alterado nesta fase | ✓ FLOWING |
| `match_batch` | `job.printer_id` | `resolve_printer_id` + Printer table | Testes com fixtures | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Testes fase 5 backend | `pytest tests/test_matcher.py … test_migrations.py -q` | 46 passed in 1.78s | ✓ PASS |
| Build frontend | `npm run build` (frontend) | tsc + vite OK | ✓ PASS |

### Probe Execution

Step 7c: SKIPPED — nenhum `probe-*.sh` declarado nos PLANs da fase 5.

### Requirements Coverage

| Requirement | Status | Evidence |
|-------------|--------|----------|
| ORG-01 – ORG-09 | ✓ SATISFIED | `departments_service`, `users_service`, `test_org_api.py`, Settings pages |
| INV-01 – INV-06 | ✓ SATISFIED | `printers_service`, matcher, registry em FilterBar |
| IMPORT-01 – IMPORT-05 | ✓ SATISFIED | `import_routes`, templates, `ImportPage` |
| SETTINGS-01 – SETTINGS-04 | ✓ SATISFIED | Rotas/sidebar; JobsPage inalterado em estrutura |
| DATA-04 – DATA-07 | ✓ SATISFIED | Alembic revision; soft-delete; WAL |
| SERVER-04 | ✓ SATISFIED | `UnmappedQueuesBanner` + registry status |

**Nota:** `.planning/REQUIREMENTS.md` ainda lista traceability "Pending" para fase 5 — documentação de planejamento desatualizada; implementação atende os IDs acima.

### Anti-Patterns Found

Nenhum BLOCKER (`TBD`/`FIXME`/`XXX` ou stub de API) nos arquivos da fase. Placeholders em formulários são labels UX, não dados vazios renderizados.

### Human Verification Required

1. **Audit dashboard após Settings** — navegar `/` ↔ `/settings/*` e validar filtros/export (ver frontmatter).
2. **CRUD Settings (4 entidades)** — criar/editar/desativar cada tipo no browser.
3. **Import CSV** — partial vs strict com arquivo real.
4. **Matcher em produção** — cadastro de impressora + jobs órfãos (P5-AC-01/02; janela 5 min).

**Nota arquitetural P5-AC-04:** O watcher roda no processo `backend` (`main.py` lifespan). Parar o container backend interrompe captura até subir de novo; impressão CUPS continua independente. O invariante D-29 (falha de matcher/import **não** quebra o handler) está verificado no código.

### Gaps Summary

Nenhum gap bloqueador identificado no código. Status `human_needed` porque critérios de aceitação UAT (P5-AC-01 a P5-AC-07) exigem validação manual no ambiente Docker/browser, conforme `05-VALIDATION.md`.

---

_Verified: 2026-05-27T18:00:00Z_  
_Verifier: Claude (gsd-verifier)_
