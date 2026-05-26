# Phase 2: Log Pipeline & Data Layer - Context

**Gathered:** 2026-05-26
**Status:** Ready for planning

<domain>
## Phase Boundary

Pipeline automático **page_log → watcher → parser → SQLite** — cada linha do `page_log` do CUPS persiste no banco sem intervenção manual. Inclui container backend (watcher + persistência + esqueleto FastAPI), volumes Docker para DB, checkpoint de retomada, schema com extensibilidade (status, policies, hook).

**Não inclui:** rotas REST públicas, Swagger, autenticação, dashboard, nginx, frontend, políticas de bloqueio ativas, UI de impressoras.

**Cadeia alvo desta fase:** CUPS (`page_log` em `cups_logs`) → backend watcher → parser → SQLite (`db_data`)

</domain>

<decisions>
## Implementation Decisions

### Granularidade no banco
- **D-01:** Persistir **uma linha por página** no SQLite — espelhamento 1:1 com cada linha do `page_log` do CUPS.
- **D-02:** **Não agregar** por job na ingestão; agregação fica para a camada de leitura (Fase 3 API / Fase 4 dashboard) via query ou view — ex.: `GROUP BY printer, job_id, username, document_name`.
- **D-03:** Parser desta fase permanece **simples** — mapear linha → registro, sem lógica de rollup.

### Checkpoint do watcher (CAPTURE-03)
- **D-04:** Persistir **inode + byte offset** do `page_log` em tabela `capture_state` no SQLite.
- **D-05:** Em restart do watcher:
  - **Mesmo inode** → `seek(offset)` e continuar tail a partir da posição salva.
  - **Inode diferente** (logrotate/arquivo novo) → reprocessar **do início do novo arquivo**.
- **D-06:** **Não** usar hash de linha nem scan completo do histórico na subida.
- **D-07:** Estratégia deve ser compatível com **logrotate futuro** sem perda de jobs durante operação normal.

### Normalização de campos do parser
- **D-08:** **Username** mantido exatamente como recebido do CUPS — ex.: `DOMAIN\usuario` (sem strip de domínio, sem lowercasing).
- **D-09:** Campos ausentes ou indisponíveis no `page_log` → **`NULL` no banco** — nunca string vazia, nunca placeholder `"unknown"`.
- **D-10:** Diferenciar semanticamente “campo inexistente na origem” de “valor conhecido” para filtros SQL e analytics futuros.

### Escopo do container backend (Fase 2)
- **D-11:** Subir **um único container `backend`** já estruturado para FastAPI (arquitetura definitiva), montando `cups_logs:ro` e volume `db_data`.
- **D-12:** **Sem** rotas REST expostas, autenticação ou Swagger nesta fase.
- **D-13:** Componentes ativos nesta fase: **watcher**, **parser**, **SQLite**, camada **repository/service**, **healthcheck interno simples** (processo/dependências — não endpoint público de API).
- **D-14:** Objetivo operacional: `page_log → watcher → parser → SQLite` **automático e resiliente**; nada de dashboard/API consumível ainda.

### Requisitos herdados (ROADMAP — não re-discutidos)
- **D-15:** `print_jobs.status` default `allowed` (EXTEND-01); tabela `policies` vazia (EXTEND-02); hook `pre_process_job` retorna `True` no MVP (EXTEND-03).
- **D-16:** Retenção configurável via `LOG_RETENTION_DAYS` (DATA-01); volumes Docker garantem persistência (DATA-02); SQLite permissões `600` (DATA-03).
- **D-17:** CUPS permanece independente se backend/watcher cair (CAPTURE-04) — watcher monta `page_log` read-only, sem interferir no spool CUPS.

### Claude's Discretion
- Schema exato de colunas em `print_jobs` além dos campos CAPTURE-01 (mapear grupos do `PAGE_LOG_REGEX` de `scripts/validate-phase1.sh`).
- Idempotência ao reprocessar arquivo novo (inode mudou) — evitar duplicatas sem usar hash de linha (ex.: constraint única composta printer+job_id+timestamp+page_index ou equivalente derivável do page_log).
- Mecanismo de purge por `LOG_RETENTION_DAYS` (startup, cron interno, ou ambos).
- Layout de pacotes Python (`backend/app/`, etc.) e process manager (watcher como thread, asyncio task, ou subprocess).
- Formato do healthcheck interno ( arquivo, socket, ou comando `docker compose exec`).
- Script `validate-phase2.sh` espelhando padrão da Fase 1.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos e roadmap
- `.planning/PROJECT.md` — Stack (Python watchdog, SQLAlchemy, SQLite), riscos de username/color_mode
- `.planning/REQUIREMENTS.md` — CAPTURE-01–04, DATA-01–03, EXTEND-01–03
- `.planning/ROADMAP.md` — Goal, success criteria e requirements da Fase 2
- `.planning/phases/01-infrastructure-print-server/01-CONTEXT.md` — Volume `cups_logs`, decisões CUPS, username AD validado

### Infraestrutura Fase 1 (integração watcher)
- `docker-compose.yml` — serviço `cups`, volume `cups_logs`; comentários para `backend` + `db_data`
- `cups/cupsd.conf.template` — `PageLogFormat` (campos disponíveis no log)
- `cups/cups-files.conf` — `PageLog /var/log/cups/page_log`
- `scripts/validate-phase1.sh` — `PAGE_LOG_REGEX` (referência SPEC §3.2) e validação username `DOMINIO\usuario`
- `docs/phase1-validation.md` — Procedimentos E2E e formato observado do `page_log`
- `.env.example` — variáveis existentes; expandir com `LOG_RETENTION_DAYS` e paths de DB

### Documentos referenciados nos planos (ausentes no repo — recuperar ou reconstruir a partir dos artefatos Fase 1)
- `SPEC.md` §3.2 — `PAGE_LOG_REGEX` e mapeamento de campos (implementação atual em `validate-phase1.sh`)
- `SPEC.md` §3.3+ — Schema SQLite, watcher, backend (se existir cópia externa, adicionar ao repo antes do plano)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/validate-phase1.sh` — `PAGE_LOG_REGEX` Python-compatible e asserts de username/impressora/timestamp; reutilizar regex e lógica de parse na implementação Python.
- `docker-compose.yml` — volume `cups_logs` já persistente; backend deve montá-lo `:ro` no mesmo path lógico `/var/log/cups/page_log`.
- `cups/cupsd.conf.template` — `PageLogFormat` define ordem dos campos: printer, user, job-id, timestamp, pages, billing (color), host, job-name, media, sides.

### Established Patterns
- Validação Nyquist via scripts bash (`validate-phase1.sh --quick` / full).
- Decisões numeradas D-NN por fase; comentários no compose indicam expansão por fase sem stubs ativos (D-03 Fase 1).
- Username remoto validado: `DOMAIN\user.example` — formato com backslash é o baseline do parser.

### Integration Points
- Watcher lê `/var/log/cups/page_log` do volume compartilhado `cups_logs` (somente leitura no backend).
- Novo volume `db_data` para SQLite persistente (DATA-02).
- Fase 3 adicionará rotas FastAPI sobre a mesma base repository/service — evitar refactor estrutural (D-11–D-13).

</code_context>

<specifics>
## Specific Ideas

- Agregação futura no dashboard: `GROUP BY printer + job_id + user + document_name`
- Checkpoint: tabela `capture_state` com inode + offset — seek no restart, reprocesso limpo em logrotate
- NULL semântico para campos ausentes — integridade do dado original
- Backend já nasce com estrutura FastAPI, mas “mudo” até a Fase 3

</specifics>

<deferred>
## Deferred Ideas

- **Agregação por job na ingestão** — rejeitada; usar queries/views nas Fases 3–4.
- **API REST / Swagger / auth** — Fase 3+.
- **Dashboard e nginx** — Fases 4–5.
- **Políticas de bloqueio ativas** — Fase 2+ (hook existe, sempre `allowed` no MVP).
- **Hash de linha ou scan completo para checkpoint** — explicitamente rejeitados pelo usuário.

</deferred>

---

*Phase: 2-Log Pipeline & Data Layer*
*Context gathered: 2026-05-26*
