# Phase 6 — Technical Research

**Researched:** 2026-05-27  
**Phase:** Costing & Chargeback  
**Status:** RESEARCH COMPLETE

---

## Summary

A Fase 6 adiciona tarifas globais com histórico de vigência, cálculo de custo no read path (por linha `print_jobs` → agregação em jobs), correção manual de `color_mode`, exports CSV de chargeback (CC + departamento) e UI Settings “Tarifas” + coluna de custo na auditoria. O hot path do watcher permanece intocado; `outside_policy` é excluído de chargeback.

**Documentação externa (Context7):**
- SQLAlchemy 2.0: `Numeric(12, 4)` / `Annotated[Decimal]` para tarifas; SQLite mapeia DECIMAL/NUMERIC; evitar `asdecimal=True` implícito em floats.
- FastAPI: `StreamingResponse(generator, media_type="text/csv")` — mesmo padrão de `export.py` existente; generator compatível com `yield_per` no SQLAlchemy.

---

## Standard Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Money | `Decimal` + SQLAlchemy `Numeric(12, 4)` | Centavos BRL; sem float drift |
| Rates history | Tabela `cost_rates` com `valid_from` | D-01/D-02; nunca UPDATE silencioso |
| Cost calc | `cost_service.py` read-path | D-22; sem materializar custo em `print_jobs` |
| Chargeback | `chargeback_export.py` + rotas `/export/chargeback/*` | Reusa padrão `csv_export.py` |
| Exclusion | Filtro `outside_policy=False` na query chargeback | D-14; reusa `policy_service` |
| CUPS | Parser aliases + doc `scripts/fix-cups-color-queue.sh` | D-05; maximizar `color_mode` na captura |

---

## Architecture

```
print_jobs (1 row = 1 página no page_log)
    │
    ├─ color_mode NULL → pages_pending (não faturável)
    ├─ color_mode mono|color + rate vigente em timestamp → linha × tarifa
    │
    ▼
jobs_service agrega → JobOut.pages_billable, pages_pending_color,
                      pages_mono, pages_color, estimated_cost
    │
    ├─ GET /jobs (auditoria)
    ├─ PATCH /jobs/lines/{id}/color-mode (correção manual)
    │
    ▼
chargeback_export (exclui outside_policy)
    ├─ by cost center (user CC override → dept CC → Não atribuído)
    ├─ by department
    └─ buckets: Usuário não cadastrado, Impressora não cadastrada, Páginas pendentes
```

### Effective rate lookup (D-02)

Para cada linha com `timestamp` T e tarifa vigente:

```python
def rate_at(db: Session, at: datetime) -> CostRate | None:
    return db.scalars(
        select(CostRate)
        .where(CostRate.valid_from <= at)
        .order_by(CostRate.valid_from.desc())
        .limit(1)
    ).first()
```

- Nova vigência = `INSERT` com novo `valid_from` (UTC ou SP — usar mesmo padrão de `print_jobs.timestamp`).
- Tarifa “atual” para Settings = última por `valid_from` global.

### Billable pages (D-06, D-07)

| `color_mode` (normalizado) | Billing |
|--------------------------|---------|
| `mono` | 1 página mono × `rate_mono` |
| `color` | 1 página color × `rate_color` |
| NULL / desconhecido | 0 faturável; conta em `pages_pending` |

**Aliases CUPS → mono** (parser ou `normalize_color_mode()`):
`grayscale`, `gray`, `grey`, `monochrome`, `bw`, `black`, `black-and-white`, `1`

**Aliases → color:**
`color`, `colour`, `rgb`, `cmyk`, `2`

**Manual correction (D-08):** `PATCH` grava `color_mode` como `mono`|`color` e `color_mode_source='manual'`.

### Chargeback attribution (D-11..D-13, D-17)

| Condição | Bucket export |
|----------|---------------|
| User ativo match `cups_username` | CC: `users.cost_center_id` ?? `departments.cost_center_id` ?? "Não atribuído" |
| Sem user ativo | "Usuário não cadastrado" |
| `printer_id` NULL | Linha também em bucket "Impressora não cadastrada" (dimensão separada no CSV) |
| `outside_policy=True` | **Excluído** de query chargeback |

### COST-04 vs D-20

- **Não** alterar `GET /stats/summary` nesta fase.
- COST-04 atendido por funções de agregação em `cost_service` / `chargeback_export` usadas pelos exports (e testes), sem dashboard gerencial.

---

## Schema

### `cost_rates`

```text
cost_rates(
  id INTEGER PK,
  rate_mono NUMERIC(12,4) NOT NULL,
  rate_color NUMERIC(12,4) NOT NULL,
  valid_from DATETIME NOT NULL,  -- início vigência (UTC naive como print_jobs)
  created_at, updated_at
)
INDEX ix_cost_rates_valid_from (valid_from DESC)
```

Sem `valid_to` calculado — vigência = maior `valid_from` ≤ evento.

### `print_jobs` (alteração)

```text
color_mode_source VARCHAR(20) NULL  -- 'captured' | 'manual'; NULL legado
```

`color_mode` passa a armazenar valores canônicos `mono`|`color`|NULL após normalização no parser ou manual.

**Migration:** `batch_alter_table('print_jobs')` no SQLite.

### Down revision

Encadear após `c4e8f1a92b03` (user_printer_access).

---

## API Surface (proposed)

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/v1/cost-rates` | Histórico (ordenado valid_from desc) |
| GET | `/api/v1/cost-rates/current` | Tarifa vigente “agora” |
| POST | `/api/v1/cost-rates` | Nova vigência (valid_from default now) |
| GET | `/api/v1/jobs` | + campos custo/páginas faturáveis |
| PATCH | `/api/v1/jobs/lines/{line_id}/color-mode` | Correção manual |
| GET | `/api/v1/export/chargeback/by-cost-center` | CSV CHRG-01 |
| GET | `/api/v1/export/chargeback/by-department` | CSV CHRG-02 |

Query params: reutilizar `JobFilters.date_from`, `date_to` (sem `outside_policy` nos exports).

---

## CSV Chargeback (CHRG-03)

- Delimitador `;`, BOM UTF-8, cabeçalhos pt-BR — igual `csv_export.py`.
- Colunas por grupo: `Grupo`, `Páginas mono`, `Páginas color`, `Custo estimado (R$)`.
- Linhas fixas no final: `Não atribuído`, `Usuário não cadastrado`, `Impressora não cadastrada`, `Páginas pendentes`.
- Cap 100k **grupos** ou linhas agregadas — mesma filosofia D-16.

---

## CUPS / Captura (D-05)

- Campo 6 do `page_log` já mapeado em `parser.py` (`color_mode`).
- Documentar em `docs/cups-color-capture.md` (ou README ops): uso de `fix-cups-color-queue.sh`, verificação `%C` no log, teste `lp -d QUEUE testpage`.
- Parser: chamar `normalize_color_mode(raw)` antes de persistir; se reconhecido → `color_mode_source='captured'`.

**Watcher invariant:** apenas `parser.py` muda; sem imports de `cost_rates` / `cost_service`.

---

## Pitfalls

| Pitfall | Mitigation |
|---------|------------|
| Usar tarifa “atual” para jobs antigos | `rate_at(timestamp)` por linha |
| `func.max(color_mode)` na agregação mistura mono+color | Agregar por `SUM(CASE WHEN color_mode='mono' THEN 1 ELSE 0 END)` na subquery de linhas |
| Chargeback inclui outside_policy | `WHERE` pré-filtro + teste dedicado |
| Float em BRL | Decimal end-to-end |
| Estender stats/summary | Explícito fora de escopo — só chargeback exports |

---

## Validation Architecture

| Property | Value |
|----------|-------|
| Framework | pytest |
| Config | `backend/pytest.ini` / `conftest.py` |
| Quick run | `cd backend && pytest -q tests/test_cost_service.py tests/test_chargeback_export.py` |
| Full suite | `cd backend && pytest -q` |
| Estimated runtime | ~15–30s |

**Critical test scenarios:**
1. Duas tarifas com `valid_from` diferentes → job antigo usa tarifa antiga.
2. Linha `color_mode` NULL → não entra em mono/color; aparece em pending.
3. PATCH manual → linha passa a faturar com tarifa vigente na data do job.
4. User fora política (`outside_policy`) → excluído do CSV chargeback.
5. User sem cadastro → bucket "Usuário não cadastrado".
6. Sem tarifa configurada → `estimated_cost` null/0, API não quebra.

---

## Plan Structure Recommendation

| Wave | Plan | Entrega |
|------|------|---------|
| 1 | 06-01 | Migration + models + parser normalization + CUPS doc |
| 2 | 06-02 | cost_service + cost_rates API |
| 3 | 06-03 | jobs enrichment + PATCH color-mode |
| 3 | 06-04 | chargeback CSV exports |
| 4 | 06-05 | Frontend Tarifas + Jobs custo/correção |

---

## RESEARCH COMPLETE
