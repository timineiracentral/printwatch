---
id: GAP-02-01
type: bug
status: pending
priority: medium
created: "2026-05-26"
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
