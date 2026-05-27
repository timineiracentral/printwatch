# Fase 3 — Verificação (Plan 03-06)

| Campo | Valor |
|-------|--------|
| status | passed-with-warnings |
| data | 2026-05-27 |
| operador | admin-user (VM SSH) |
| ambiente | VM printwatch-dev, `BASE_URL=http://localhost:8000` |

## Resumo

| Dimensão | Resultado |
|----------|-----------|
| `validate-phase3.sh --quick` (VM) | 17 PASS / 0 FAIL / 1 WARN (pytest skip no host) |
| Checkpoint #17 — job na API | ✓ Operador confirmou via `curl /api/v1/jobs` |
| Checkpoint #17 — CSV download | ✓ `curl …/export/csv` → `/tmp/printwatch_test.csv` (2286 bytes) |
| Checkpoint #17 — Excel pt-BR | ⚠ Não executado na VM (sem GUI); validação estrutural via CLI abaixo |
| GAP-02-02 | ✓ Fechado — investigação observacional (classificação a, recomendação 1) |
| EXPORT-01 / EXPORT-02 | ✓ Evidência parcial CLI + download OK |
| DASH-06 | ✓ EXPLAIN usa `idx_print_jobs_timestamp`; `/jobs` responde em &lt;100ms na VM (86–22 rows) |

## validate-phase3.sh — quick (VM)

Executado anteriormente na sessão do agente:

```
17 PASS / 0 FAIL / 1 WARN
WARN: pytest não disponível no host da VM (esperado — testes rodam no dev host)
```

## Checkpoint #17 — evidência operador

### Jobs na API

Operador executou:

```bash
curl 'http://localhost:8000/api/v1/jobs' | python3 -m json.tool | head -40
```

Confirmado: jobs recentes visíveis com `printer`, `username`, `timestamp` (fuso `-03:00`), `host_origin`, agregação por job.

### CSV export

Operador executou:

```bash
curl 'http://localhost:8000/api/v1/export/csv' -o /tmp/printwatch_test.csv
```

Download concluído (2286 bytes).

### Validação estrutural CSV (CLI — substituto Excel na VM)

| Check | Evidência |
|-------|-----------|
| BOM UTF-8 | `xxd` início: `ef bb bf` |
| Separador `;` | Header: `Data/Hora;Usuário;Impressora;Documento;Páginas;…` |
| Headers pt-BR | `Usuário`, `Páginas`, `Frente/Verso`, `Origem` presentes |
| Content-Type | `text/csv; charset=utf-8` |
| Content-Disposition | `attachment; filename="print_jobs_YYYYMMDD_HHMM.csv"` |
| X-Total-Rows | 22 (alinhado ao volume agregado na VM) |
| Linhas de teste | Timestamps 2026-05-27 09:34 e 09:45 no CSV |

**Nota Excel:** abertura no Excel Windows pt-BR permanece recomendada no próximo acesso a estação com GUI; estrutura atende EXPORT-02 (BOM + `;` + acentos UTF-8 no arquivo).

## Performance (amostra VM)

| Endpoint | Observação |
|----------|------------|
| `GET /api/v1/jobs?size=50` | Resposta imediata em DB ~86 rows brutos / ~22 agregados |
| `GET /api/v1/export/csv` | Stream ~2 KB em &lt;1s |

## GAP-02-02

Ver `.planning/phases/03-backend-api/03-INVESTIGATION-username-ad.md` (local, gitignored) e `.planning/todos/resolved/GAP-02-02-username-domain-ad.md`.

## Falhas abertas

Nenhuma bloqueante para fechar Fase 3.

## Assinatura

Fase 3 considerada **aprovada para transição** com ressalva documentada (Excel manual opcional). Atualizar `STATE.md` / ROADMAP na próxima sessão de milestone se aplicável.
