---
phase: 06-costing-chargeback
reviewed: 2026-05-27T23:30:00Z
depth: standard
files_reviewed: 27
files_reviewed_list:
  - backend/alembic/versions/4227505c4a72_cost_rates.py
  - backend/app/db/models.py
  - backend/app/services/color_mode.py
  - backend/app/services/parser.py
  - backend/app/services/cost_service.py
  - backend/app/schemas/cost_rates.py
  - backend/app/api/v1/cost_rates.py
  - backend/app/api/v1/__init__.py
  - backend/app/services/jobs_service.py
  - backend/app/schemas/jobs.py
  - backend/app/schemas/job_lines.py
  - backend/app/api/v1/jobs.py
  - backend/app/services/chargeback_export.py
  - backend/app/api/v1/export.py
  - frontend/src/pages/settings/CostRatesPage.tsx
  - frontend/src/api/settings/costRates.ts
  - frontend/src/hooks/useCostRates.ts
  - frontend/src/hooks/useShowCostColumn.ts
  - frontend/src/components/jobs/ColorModeCorrectionModal.tsx
  - frontend/src/components/export/ChargebackExportButtons.tsx
  - frontend/src/components/jobs/JobsTable.tsx
  - frontend/src/pages/JobsPage.tsx
  - frontend/src/types/api.ts
  - frontend/src/routes/index.tsx
  - frontend/src/components/layout/Sidebar.tsx
  - frontend/src/api/jobs.ts
  - frontend/src/lib/format.ts
findings:
  critical: 0
  warning: 5
  info: 2
  total: 7
status: issues_found
---

# Phase 6: Code Review Report

**Reviewed:** 2026-05-27T23:30:00Z  
**Depth:** standard  
**Files Reviewed:** 27  
**Status:** issues_found

## Summary

Revisão adversarial da fase **06-costing-chargeback** (planos 01–05): schema `cost_rates`, `cost_service`, enriquecimento de jobs, exports chargeback e UI de tarifas/custo. A arquitetura segue o desenho de `06-CONTEXT.md` (Decimal no read path, `outside_policy` fora do chargeback, watcher sem costing). Não foram encontrados bloqueadores de correção ou segurança novos além do modelo já aberto da API (sem auth nas rotas v1).

Há **5 warnings** concentrados em vigência de tarifa (timezone), parâmetros de export ignorados, integridade de `color_mode` no chargeback, duplicidade de vigências e feedback de erro na correção manual. Nenhum exige rollback, mas convém corrigir antes de UAT financeiro.

## Warnings

### WR-01: `valid_from` da UI gravado como meia-noite naive (desvio de SP)

**File:** `frontend/src/pages/settings/CostRatesPage.tsx:47-48`, `backend/app/services/cost_service.py:257-261`  
**Issue:** O formulário envia `valid_from` como `YYYY-MM-DDT00:00:00` sem offset. O backend só converte para UTC quando `tzinfo` está presente; caso contrário persiste o naive tal qual. Timestamps de jobs vêm do CUPS com fuso e são comparados em `rate_at` como naive UTC. Operadores em `America/Sao_Paulo` podem ver a vigência efetiva ~3 h antes do dia civil esperado.  
**Fix:** Converter a data local para UTC no backend (reutilizar `_local_date_to_utc_range`) ou enviar ISO com offset:

```python
# cost_service.create_cost_rate — após parse do payload
if payload.valid_from is not None and payload.valid_from.tzinfo is None:
    start_utc, _ = _local_date_to_utc_range(payload.valid_from.date())
    valid_from = start_utc.replace(tzinfo=None)
```

### WR-02: Export chargeback envia filtros que a API ignora

**File:** `frontend/src/components/export/ChargebackExportButtons.tsx:11-21`, `backend/app/services/chargeback_export.py:37-45`  
**Issue:** `exportFiltersToSearchParams` inclui `username`, `printer` e `search`, mas `aggregate_cost_by_dimension` só filtra por intervalo de datas. Usuário na JobsPage com filtros ativos pode acreditar que o CSV reflete a tabela visível; o arquivo cobre o mês/período inteiro.  
**Fix:** Remover parâmetros não suportados no frontend **ou** documentar na UI (“exporta o período completo”) **ou** aplicar os mesmos filtros no serviço de agregação.

### WR-03: `color_mode` inválido some do chargeback (nem bucket pendente)

**File:** `backend/app/services/cost_service.py:162-167`  
**Issue:** Valores fora de `mono`/`color`/`NULL` caem no `continue` sem incrementar `pages_pending` nem grupos normais. Páginas com dado corrompido ou legado desaparecem dos totais CSV sem rastro.  
**Fix:** Tratar como pendente ou bucket de exceção:

```python
else:
    row = _ensure_bucket(buckets, "_pending_pages", BUCKET_PENDING_PAGES)
    row["pages_pending"] += 1
    continue
```

### WR-04: Vigências duplicadas em `cost_rates` sem restrição

**File:** `backend/app/services/cost_service.py:257-273`, `backend/alembic/versions/4227505c4a72_cost_rates.py`  
**Issue:** Não há `UNIQUE(valid_from)` nem checagem em `create_cost_rate`. Duas linhas com o mesmo `valid_from` fazem `rate_at` depender da ordem arbitrária do SQLite.  
**Fix:** Índice único em `valid_from` + `HTTP 409` se já existir vigência naquele instante.

### WR-05: PATCH de cor sem feedback de erro na UI

**File:** `frontend/src/components/jobs/ColorModeCorrectionModal.tsx:95-107`  
**Issue:** `patch.mutateAsync` é chamado com `void` e sem `onError`/banner. Falha de rede ou 404 deixa o operador sem indicação; a linha continua pendente.  
**Fix:** Usar `onError` na mutation ou `try/catch` com `ErrorBanner` / toast, e desabilitar botões só durante `isPending`.

## Info

### IN-01: `estimated_cost` serializado como `float` na API

**File:** `backend/app/schemas/jobs.py:54-58`  
**Issue:** Conversão `float(Decimal)` pode introduzir ruído binário em valores BRL (ex.: 0.1 + 0.2). Impacto baixo na UI que formata com 2 casas.  
**Fix:** Serializar como string decimal (`"0.20"`) ou usar `Decimal` no JSON schema Pydantic v2.

### IN-02: `aggregate_cost_by_dimension` chama `rate_at` por linha

**File:** `backend/app/services/cost_service.py:150-155`  
**Issue:** Uma query SQL por job no intervalo; export faz contagem + iteração (duas passagens completas). Correto funcionalmente; pode degradar em bases grandes. Fora do escopo v1 de performance, mas vale cache `{timestamp: rate}` no loop.  
**Fix:** Cache local `rate_cache: dict[datetime, CostRate | None]` keyed por timestamp (ou por `valid_from` vigente).

---

_Reviewed: 2026-05-27T23:30:00Z_  
_Reviewer: Claude (gsd-code-reviewer)_  
_Depth: standard_
