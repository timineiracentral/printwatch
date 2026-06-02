# Runbook — Manager Analytics (Fase 7)

Operação do painel gerencial (`/manager`) e leituras de contador físico.

## Pré-requisitos

### Classificação `color_mode` nos jobs

KPIs faturáveis e custos dependem de `print_jobs.color_mode` preenchido. Sem isso, páginas entram como **pendentes** e um banner aparece no painel quando >5% do volume está pendente.

- Guia CUPS: [cups-color-capture.md](./cups-color-capture.md)
- Correção manual por linha: modal na auditoria de jobs (Fase 6)

### Migration e índice de performance

Na VM ou ambiente de deploy:

```bash
cd backend
export DB_PATH=/app/data/printwatch.db   # dentro do container backend
python -m alembic upgrade head
```

Confirme a revision `printer_meter_readings` e o índice `ix_print_jobs_timestamp` (meta ANAL-04: summary 90 dias <3s).

## Painel gerencial (`/manager`)

- Filtros na URL (`date_from`, `date_to`, `preset`) — padrão ao abrir: últimos 30 dias.
- Preset **Mês atual** envia `preset=month` para comparativo com mês calendário anterior (timezone `America/Sao_Paulo`).
- Jobs com `outside_policy` não entram em totais nem rankings.
- `/stats/summary` na home **não** foi alterado.

## Leitura manual de contador (METER-01)

1. **Settings → Impressoras** → botão **Contador** na impressora ativa, ou
2. API: `POST /api/v1/printers/{id}/meter-readings` com JSON:

```json
{
  "timestamp": "2026-06-02T12:00:00Z",
  "counter_total": 150000,
  "counter_mono": 90000,
  "counter_color": 60000,
  "source": "manual"
}
```

## Import CSV de leituras (METER-02)

`POST /api/v1/import/meter-readings` (multipart, campo `file`).

Cabeçalho obrigatório:

```text
printer_code,counter_total,timestamp,counter_mono,counter_color
```

- `printer_code`: fila CUPS (`cups_queue_name`) ou nome de exibição cadastrado
- `timestamp`: ISO-8601 (ex.: `2026-06-01T08:00:00Z`)

Campos que começam com `=`, `+`, `-`, `@` são sanitizados contra CSV injection.

## Reconciliação contador vs jobs (METER-05)

Tabela **Contador vs jobs** no painel:

| Coluna | Significado |
|--------|-------------|
| Pág. contador | Delta entre leitura inicial e final no período |
| Pág. jobs | Linhas faturáveis (`mono`/`color`) da impressora, excl. `outside_policy` |
| Divergência | Diferença percentual informativa (limiar 5%) |

**Não** alimenta chargeback nem export contábil (D-28). Divergência alta indica conferência operacional, não erro de faturamento.

### Intervalo parcial / reset

- **Intervalo parcial**: sem leitura antes do início do período — usa primeira leitura dentro do intervalo.
- **Reset contador**: leitura final menor que inicial — delta zerado, flag na UI.

## SNMP / poll automático

**Fora do escopo da Fase 7.** Coleta automática de contadores via SNMP está prevista para Fase 8 (Fleet Health).

## Troubleshooting performance

- Verifique índice: `EXPLAIN QUERY PLAN` em consultas por `print_jobs.timestamp`
- Dataset muito grande: considere retenção de jobs e WAL SQLite na VM
- Benchmark local: `pytest tests/test_manager_service.py::test_summary_90d_under_3s`

## Checklist UAT

Ver `.planning/phases/07-manager-analytics/07-HUMAN-UAT.md` e executar via `/gsd-verify-work`.
