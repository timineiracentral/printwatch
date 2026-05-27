---
phase: 06-costing-chargeback
verified: 2026-05-27T23:45:00Z
status: passed
score: 5/5
overrides_applied: 0
re_verification: false
---

# Phase 6: Costing & Chargeback Verification Report

**Phase Goal:** Costing & Chargeback — global rates, billable pages, internal CSV chargeback, UI.  
**Verified:** 2026-05-27T23:45:00Z  
**Status:** passed  
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Admin define tarifa global mono e color | ✓ VERIFIED | `CostRate` model + migration `4227505c4a72`; API `GET/POST /api/v1/cost-rates`, `GET /current`; `create_cost_rate` insere vigência sem DELETE; UI `CostRatesPage` + `useCostRates`; `test_cost_rates_crud_and_history` |
| 2 | Lista de jobs exibe custo estimado quando rates configurados | ✓ VERIFIED | `JobOut.estimated_cost` + `_enrich_estimated_cost` em `jobs_service.py`; `test_job_out_estimated_cost_with_rates`; `JobsTable` coluna com toggle `printwatch.showCostColumn` e `formatEstimatedCost` |
| 3 | Export chargeback CSV por CC e departamento com split mono/color | ✓ VERIFIED | `GET /export/chargeback/by-cost-center` e `by-department`; `chargeback_export.iter_chargeback_csv` com header mono/color/custo; `test_export_chargeback_endpoints_return_csv_with_bom` |
| 4 | Bucket "não atribuído" visível para jobs/usuários sem cadastro | ✓ VERIFIED | `BUCKET_UNASSIGNED_CC = "Não atribuído"` em `aggregate_cost_by_dimension` quando usuário sem `cost_center_id` efetivo; buckets adicionais testados: `Usuário não cadastrado`, `Impressora não cadastrada`, `Páginas pendentes` |
| 5 | Nenhuma geração de fatura ou integração contábil | ✓ VERIFIED | Exports são `StreamingResponse` CSV interno; grep sem `invoice`/`fatura`/`accounting` no backend de chargeback |

**Score:** 5/5 truths verified

### Plan Must-Haves (Cross-Plan)

| Truth | Status | Evidence |
|-------|--------|----------|
| D-02 `rate_at(timestamp)` usa tarifa vigente no evento | ✓ VERIFIED | `cost_service.rate_at`; `test_rate_at_uses_older_vigencia_when_event_before_new_rate` |
| D-08 PATCH manual `color_mode` + `source=manual` | ✓ VERIFIED | `PATCH /jobs/lines/{id}/color-mode`; `test_patch_null_to_mono_updates_aggregated_job` |
| D-14 `outside_policy` excluído do chargeback | ✓ VERIFIED | `compute_outside_policy` skip em `aggregate_cost_by_dimension`; `test_outside_policy_job_excluded_from_chargeback` |
| D-20 `/stats/summary` sem custo | ✓ VERIFIED | `test_stats_service_has_no_estimated_cost`; `stats.py` inalterado |
| Watcher sem imports de costing | ✓ VERIFIED | grep vazio em `backend/app/watcher/` |
| Parser CUPS → mono\|color\|NULL | ✓ VERIFIED | `color_mode.normalize_color_mode` + integração em `parser.py`; `test_color_mode.py` |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/alembic/versions/4227505c4a72_cost_rates.py` | Migration cost_rates + color_mode_source | ✓ VERIFIED | Tabela + índice `valid_from` |
| `backend/app/services/cost_service.py` | Read-path costing + agregação | ✓ VERIFIED | 274 linhas; Decimal; buckets D-11..D-14 |
| `backend/app/services/chargeback_export.py` | CSV chargeback streaming | ✓ VERIFIED | BOM UTF-8, delimitador `;` |
| `backend/app/api/v1/cost_rates.py` | CRUD tarifas | ✓ VERIFIED | Wired em `api_v1_router` |
| `backend/app/api/v1/export.py` | Rotas chargeback | ✓ VERIFIED | Dois endpoints + cap 100k |
| `backend/app/schemas/jobs.py` | JobOut cost fields | ✓ VERIFIED | `pages_billable`, `estimated_cost`, etc. |
| `frontend/src/pages/settings/CostRatesPage.tsx` | Settings Tarifas | ✓ VERIFIED | Form vigência + histórico BRL |
| `frontend/src/components/jobs/JobsTable.tsx` | Coluna custo + correção | ✓ WIRED | Importa modal; render condicional |
| `frontend/src/components/export/ChargebackExportButtons.tsx` | Downloads CSV | ✓ WIRED | Usado em `JobsPage.tsx` |
| `docs/cups-color-capture.md` | Runbook CUPS | ✓ VERIFIED | Arquivo presente |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `JobsTable.tsx` | `/api/v1/jobs` | `useJobs` hook | ✓ WIRED | Exibe `estimated_cost` quando toggle ativo |
| `ChargebackExportButtons.tsx` | `/export/chargeback/*` | `window.open` + filtros URL | ✓ WIRED | Repassa `date_from`/`date_to` de `useUrlFilters` |
| `CostRatesPage.tsx` | `/api/v1/cost-rates` | `useCostRates` | ✓ WIRED | POST nova vigência + lista histórico |
| `export.py` | `chargeback_export` | `StreamingResponse(iter_chargeback_csv)` | ✓ WIRED | |
| `chargeback_export` | `aggregate_cost_by_dimension` | import direto | ✓ WIRED | |
| `jobs_service` | `cost_service.rate_at/line_cost` | `_sum_estimated_cost` | ✓ WIRED | Cache por timestamp |
| `parser.py` | `color_mode.normalize_color_mode` | parse page_log field 6 | ✓ WIRED | |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `JobsTable` cost column | `job.estimated_cost` | `GET /jobs` → `_enrich_estimated_cost` → `rate_at` + `line_cost` por linha DB | ✓ | ✓ FLOWING |
| Chargeback CSV | row `estimated_cost` | `aggregate_cost_by_dimension` loop `PrintJob` + `rate_at` | ✓ | ✓ FLOWING |
| `CostRatesPage` vigente | `current.data` | `GET /cost-rates/current` | ✓ | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Suite fase 6 (32 testes) | `pytest tests/test_color_mode.py tests/test_cost_service.py tests/test_cost_rates.py tests/test_jobs_cost.py tests/test_jobs_color_patch.py tests/test_chargeback_export.py -q` | 32 passed in 3.98s | ✓ PASS |
| Endpoints chargeback retornam BOM | `test_export_chargeback_endpoints_return_csv_with_bom` | 200 + `\xef\xbb\xbf` | ✓ PASS |

### Probe Execution

Step 7c: SKIPPED — fase não declara probes `scripts/*/tests/probe-*.sh`.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| COST-01 | 01, 02, 05 | Admin configura tarifa global mono/color | ✓ SATISFIED | API + UI Tarifas |
| COST-02 | 01, 02, 03 | Custo estimado por páginas + modo cor + tarifa vigente | ✓ SATISFIED | `line_cost`, `rate_at`, parser |
| COST-03 | 03, 05 | API/UI expõe custo em jobs | ✓ SATISFIED | `JobOut` + coluna opcional |
| COST-04 | 02, 04 | Stats endpoint agrega custo por dept/CC/user | ⚠️ PARTIAL | `aggregate_cost_by_dimension` cobre **CC + dept** nos exports; **sem** dimensão `user` e **sem** extensão de `/stats/summary` — alinhado a D-20/06-CONTEXT (Fase 7), diverge do texto literal em REQUIREMENTS.md |
| CHRG-01 | 04, 05 | Export CSV por centro de custo | ✓ SATISFIED | `/export/chargeback/by-cost-center` |
| CHRG-02 | 04, 05 | Export CSV por departamento | ✓ SATISFIED | `/export/chargeback/by-department` |
| CHRG-03 | 04 | mono/color split, custo, buckets | ✓ SATISFIED | Header + buckets em `cost_service` |
| CHRG-04 | 04 | Só relatório interno | ✓ SATISFIED | Sem invoice/accounting |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | Nenhum TBD/FIXME/XXX em arquivos da fase | — | — |

### Human Verification Recommended (non-blocking)

Itens operacionais da `06-VALIDATION.md` não bloqueiam o goal da fase (lógica verificada por testes):

1. **CUPS color real** — imprimir testpage após `fix-cups-color-queue.sh`; confirmar `color_mode` capturado no log.
2. **Settings Tarifas UX** — criar vigência futura; confirmar formatação `R$` e ordem do histórico.

### Gaps Summary

Nenhum gap bloqueador. A fase entrega o contrato do ROADMAP (5/5). **COST-04** permanece parcial em relação ao texto de REQUIREMENTS.md (`stats` + agregação por **usuário**); a implementação segue decisão explícita D-20 (custo fora de `/stats/summary` nesta fase) e `aggregate_cost_by_dimension` nos exports. Recomenda-se atualizar REQUIREMENTS.md ou tratar agregação por usuário na Fase 7.

---

_Verified: 2026-05-27T23:45:00Z_  
_Verifier: Claude (gsd-verifier)_
