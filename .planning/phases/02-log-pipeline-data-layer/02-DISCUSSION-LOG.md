# Phase 2: Log Pipeline & Data Layer - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-26
**Phase:** 2-Log Pipeline & Data Layer
**Areas discussed:** Granularidade no banco, Checkpoint do watcher, Normalização de campos, Escopo do backend

---

## Granularidade no banco

| Option | Description | Selected |
|--------|-------------|----------|
| Uma linha por job (agregado) | Parser soma páginas; uma row por job no SQLite | |
| Uma linha por página | Espelha 1:1 o page_log do CUPS; agregação só na leitura | ✓ |
| Híbrido | Persistir ambos job + page tables | |

**User's choice:** Uma linha por página — fidelidade à origem, auditoria, reprocessamento simples; agregação via `GROUP BY printer + job_id + user + document_name` na Fase 4.

**Notes:** Reduz complexidade do parser nesta fase.

---

## Checkpoint do watcher após restart

| Option | Description | Selected |
|--------|-------------|----------|
| Offset + inode em SQLite | `capture_state` com inode e byte offset; seek ou reprocesso se inode mudou | ✓ |
| Hash de linha | Dedup por hash do conteúdo | |
| Scan completo | Reler arquivo inteiro e comparar com DB | |
| Último job-id global | Bookmark por ID CUPS | |

**User's choice:** Offset + inode em tabela `capture_state`. Mesmo inode → seek(offset). Inode mudou → reprocessar do início do novo arquivo. Compatível com logrotate.

**Notes:** Explicitamente rejeitou hash de linha e scan completo.

---

## Normalização de campos

| Option | Description | Selected |
|--------|-------------|----------|
| Username as-is | Manter `DOMAIN\usuario` exatamente como CUPS envia | ✓ |
| Strip domínio | Normalizar para só `usuario` | |
| Campos ausentes → NULL | Sem string vazia ou `"unknown"` | ✓ |
| Campos ausentes → default string | `"unknown"` ou `""` | |

**User's choice:** Username intacto; campos ausentes sempre `NULL`.

**Notes:** Diferencia campo inexistente de valor conhecido para SQL/analytics.

---

## Escopo do backend nesta fase

| Option | Description | Selected |
|--------|-------------|----------|
| Só watcher + SQLite | Container mínimo sem FastAPI | |
| Backend estruturado FastAPI (mudo) | Watcher + parser + repo/service + healthcheck interno; sem REST/Swagger/auth | ✓ |
| Backend com API esqueleto exposta | Rotas stub já publicadas | |

**User's choice:** Container único já estruturado para FastAPI — watcher, parser, SQLite, repository/service, healthcheck interno. Sem rotas REST, auth ou Swagger.

**Notes:** Evita refactor na Fase 3; objetivo = pipeline automático e resiliente.

---

## Claude's Discretion

- Schema detalhado de `print_jobs` e idempotência ao reprocessar após logrotate (sem hash de linha)
- Mecanismo de purge `LOG_RETENTION_DAYS`
- Layout de pacotes e forma do healthcheck interno
- Script `validate-phase2.sh`

## Deferred Ideas

- Agregação por job na ingestão → queries/views Fases 3–4
- API, dashboard, políticas ativas → fases posteriores
