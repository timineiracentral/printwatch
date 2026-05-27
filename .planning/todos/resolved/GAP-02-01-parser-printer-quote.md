---
id: GAP-02-01
type: bug
status: resolved
priority: medium
created: "2026-05-26"
resolved: "2026-05-26"
resolved_in: 03-02
phase_origin: 02-log-pipeline-data-layer
resolves_phase: "3"
source_evidence: "DB query 2026-05-26 19:58:49 — printer field = \"test_printer (com aspa inicial)"
component: backend/app/services/parser.py
---

# GAP-02-01 — Parser captura aspa inicial em `printer`

## Sintoma

Jobs gravados no banco mostram campo `printer` com aspa dupla no início:

```
2026-05-26 19:58:49 | user.example | "test_printer | Página de teste | pages=0 | status=allowed
```

Esperado: `printer = test_printer` (sem aspa).

## Hipótese provável

O `PageLogFormat` no `cupsd.conf.template`:

```
PageLogFormat "%p %u %j %T %P %C %{job-billing} %{job-originating-host-name} %{job-name} %{media} %{sides}"
```

CUPS pode emitir aspas em torno de campos que contêm espaços (ex: `%{job-name}` = `"Página de teste"`).
O `PAGE_LOG_REGEX` em `backend/app/services/parser.py` usa `(\S+)` para `printer` no início,
o que pode estar capturando aspa quando a linha inteira tem aspas externas no log do CUPS.

## Investigação necessária antes do fix

1. Capturar linha bruta do `/var/log/cups/page_log` correspondente ao job ID 4
2. Identificar se a aspa está:
   - (a) no início da linha (CUPS quoting toda a linha)
   - (b) só no `job-name` (CUPS quoting campo com espaço)
3. Ajustar `PAGE_LOG_REGEX` ou pré-processar a linha (strip de aspas) conforme evidência

## Ajuste provável

- Strip de aspas em todos os campos string após `_null_if_dash`
- OU ajustar regex para tolerar aspas opcionais nos campos

## Tracking

- Reproduzir com `docker compose exec cups tail -n 1 /var/log/cups/page_log`
- Adicionar teste regressão em `backend/tests/test_parser.py` com a linha bruta capturada
- Resolver até a entrega da Fase 3

## Impacto

Médio — dado fica usável (filtros funcionam com `LIKE`), mas relatórios e API expõem o valor corrompido.
Não bloqueia Fase 3, mas deve ser resolvido antes da entrega do Dashboard (Fase 4).

## Resolução (2026-05-26 — Plano 03-02)

**Causa raiz observada** (`.planning/phases/03-backend-api/03-INVESTIGATION-printer-quote.md`):
`PageLogFormat "..."` no `cupsd.conf.template` envelopa cada linha do
`/var/log/cups/page_log` em aspas duplas. Classificação **(a) Linha
completa do page_log tem aspas externas**. Evidência bruta da VM
VM_HOST capturada e anexada à investigação.

**Fix aplicado (3 camadas):**

1. **`backend/app/services/normalization.py`** — `normalize_printer_name`
   idempotente, com docstring referenciando GAP-02-01.
2. **`backend/app/services/parser.py`** — `parse_page_log_line` aplica
   `normalize_printer_name(m.group(1))` no campo `printer`.
3. **`backend/scripts/backfill_printer_quotes.py`** — script standalone
   idempotente que limpa o volume `db_data` existente. Executado na VM:
   `before=86 after=0 fixed=86` na 1ª run; `nothing to do` na 2ª run.

**Testes adicionados:**

- `backend/tests/test_normalization.py` — 12 testes (RED→GREEN gate
  validado), incluindo idempotência parametrizada com 6 inputs.
- `backend/tests/test_parser.py::test_parser_strips_printer_quote_regression_gap_02_01`
  — teste de regressão com a linha bruta capturada do page_log real.

**Estado final do DB observado (VM_HOST):**

| Item | Antes | Depois |
|---|---|---|
| `SELECT DISTINCT printer` | `'"test_printer'` | `'test_printer'` |
| Linhas com aspa no `printer` | 86 / 86 | 0 / 86 |
| Suite pytest backend | 24 passed | 37 passed |

**Observação fora do escopo deste GAP** (registrada na investigação):
o `sides` também sofre da mesma causa raiz (`-"` e `one-sided"`).
Plano 03-02 escopou somente `printer`. Sugestão: GAP cosmético
adicional na fase de manutenção, ou correção da causa raiz removendo
as aspas do `PageLogFormat` em `cups/cupsd.conf.template` (Fase 5).
