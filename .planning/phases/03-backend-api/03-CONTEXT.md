# Phase 3: Backend API - Context

**Gathered:** 2026-05-26
**Status:** Ready for planning

<domain>
## Phase Boundary

API REST FastAPI servindo os dados já capturados pela Fase 2 (`print_jobs` em SQLite) — listagem agregada **por job** com filtros/paginação, estatísticas, exportação CSV e listagem informacional de impressoras. Esta fase **abre** as rotas públicas, habilita o Swagger no container `backend` existente e fecha os dois gaps de qualidade de dado herdados da Fase 2.

**Cadeia alvo desta fase:** `SQLite (Fase 2) → SQLAlchemy queries → FastAPI routes → JSON/CSV (UTF-8 BOM) → curl/Fase 4 dashboard`

**Não inclui:** dashboard React/Vite, nginx proxy, autenticação, UI de adicionar impressoras (SERVER-04 → Fase 5), runtime/online-offline polling do CUPS, materialized views, FTS5, XLSX, async SQLAlchemy, Redis, Celery, Postgres.

</domain>

<decisions>
## Implementation Decisions

### A. Endpoint `/api/v1/jobs` — agregação, paginação, filtros, ordenação

- **D-01:** API principal trabalha em **granularidade por job** (não por página). O banco continua intocado em 1 linha por página (D-01 Fase 2 preservada).
- **D-02:** Agregação feita via **query SQL** (`GROUP BY`), não via view materializada nem coluna calculada. Sem alteração no schema da Fase 2 nesta etapa.
- **D-03:** `pages = COUNT(*)` por grupo agregado (uma linha do `page_log` = uma página impressa).
- **D-04:** Chave de agregação: `(printer_normalized, job_id, username, job_name, timestamp_window)`, onde `printer_normalized` aplica o fix do GAP-02-01 (ver D-22).
- **D-05:** `timestamp_window` = `timestamp` **truncado por minuto** (`strftime('%Y-%m-%d %H:%M', timestamp)` em SQLite). Suficiente para colapsar páginas do mesmo job sem agrupar jobs distintos.
- **D-06:** Timestamp do job agregado retornado pela API = `MIN(timestamp)` do grupo (primeira página).
- **D-07:** Ordem default: `timestamp DESC` (jobs mais recentes primeiro).
- **D-08:** Paginação: query params `?page=<int>&size=<int>`; defaults `page=1`, `size=50`; máximo `size=500`. Resposta inclui `total` (contagem agregada), `page`, `size`, `items`.
- **D-09:** Filtros (todos opcionais, combináveis com AND):
  - `username` — **contains, case-insensitive** (`LOWER(username) LIKE LOWER('%term%')`).
  - `printer` — **exact match** sobre o `printer_normalized` (sem aspas, ver D-22).
  - `search` — `job_name LIKE '%term%'` (case-insensitive); **sem FTS5 nesta fase**.
  - `date_from` / `date_to` — **inclusivos nas duas pontas**.
- **D-10:** Timezone — banco persiste em **UTC** (`TIMESTAMP` SQLite naive interpretado como UTC, alinhado com `purge_old_jobs` em `app/services/retention.py`). Camada API converte para **`America/Sao_Paulo`** apenas na serialização (response) e na **interpretação de `date_from`/`date_to`** (input do usuário). Banco e queries continuam em UTC.

### B. Endpoint `/api/v1/export/csv`

- **D-11:** CSV usa o **mesmo dataset agregado por job** da `/jobs` (mesma camada de service/query). Filtros aceitos: idênticos a `/jobs` (`username`, `printer`, `search`, `date_from`, `date_to`).
- **D-12:** Encoding: **UTF-8 com BOM** (`\ufeff` prefix) — Excel Windows pt-BR abre corretamente sem prompt de import.
- **D-13:** Delimitador: **`;`** (Excel pt-BR default).
- **D-14:** Cabeçalhos em **pt-BR amigável**:
  `Data/Hora` ; `Usuário` ; `Impressora` ; `Documento` ; `Páginas` ; `Papel` ; `Frente/Verso` ; `Modo de Cor` ; `Origem`
- **D-15:** `StreamingResponse` (FastAPI/Starlette) — não materializar o CSV inteiro em memória. Yield linha a linha do cursor SQL.
- **D-16:** Limite hard: **100.000 linhas**. Se a query agregada exceder, retornar `400` com mensagem `"Resultado excede 100k linhas — refine os filtros (date_from/date_to ou username)"`. Sem paginação no CSV (CSV é dump único).
- **D-17:** Nome do arquivo via `Content-Disposition: attachment; filename="print_jobs_YYYYMMDD_HHMM.csv"` (timestamp local America/Sao_Paulo do momento do request).
- **D-18:** Sem XLSX nesta fase.
- **D-19:** **Estrutura interna preparada** para `?granularity=page|job` futuro (camada de service aceita o parâmetro), mas **o query param NÃO é exposto** na API pública agora. Decisão revisitável em fases futuras sem refactor.

### C. Endpoints `/api/v1/stats/summary` + `/api/v1/printers`

- **D-20:** `/stats/summary` — definições temporais:
  - Timezone: **`America/Sao_Paulo`** para definir os bounds; query final converte para UTC antes de filtrar.
  - **"Hoje"** = dia calendário local (00:00:00 → 23:59:59 em America/Sao_Paulo).
  - **"Mês"** = mês calendário corrente (1º dia 00:00 até último dia 23:59:59 em America/Sao_Paulo) — **NÃO** rolling 30d.
  - **Top usuários** e **top impressoras** ordenados por `SUM(pages)` do dataset agregado por job (i.e., total de páginas impressas).
  - Default `top=5`.
  - Janelas retornadas: `hoje`, `mes`, `total` (todo o histórico no banco).
  - Schema de resposta sugerido:
    ```json
    {
      "hoje":  { "jobs": N, "pages": N, "top_users": [...], "top_printers": [...] },
      "mes":   { "jobs": N, "pages": N, "top_users": [...], "top_printers": [...] },
      "total": { "jobs": N, "pages": N, "top_users": [...], "top_printers": [...] }
    }
    ```
- **D-21:** `/printers` — fonte:
  - **`DISTINCT printer FROM print_jobs`** (com `printer_normalized` já aplicado, ver D-22).
  - **Não** consultar CUPS via `lpstat`, IPP CUPS-Get-Printers, nem socket dentro desta fase — evita acoplamento backend ↔ runtime CUPS.
  - **Não** implementar `online/offline` aqui — fica para Fase 5 SERVER-04.
  - Endpoint é puramente **informacional/histórico** (impressoras que já registraram pelo menos 1 job). Resposta: lista plana de strings ordenadas alfabeticamente.

### D. Resolução dos GAPs da Fase 2

- **D-22:** **GAP-02-01 (aspa em `printer`) — corrigir AGORA.**
  - Criar função `normalize_printer_name(raw: str) -> str` em `app/services/parser.py` (ou módulo dedicado `app/services/normalization.py`) que faz `strip()` + remove aspas duplas/simples extremas idempotentemente.
  - Aplicar no **parser** (`parse_page_log_line`) → garante dados novos limpos.
  - **Backfill do SQLite existente** via **script/migration explícito e idempotente** em `backend/migrations/` (ou `backend/scripts/`): `UPDATE print_jobs SET printer = TRIM(...) WHERE printer LIKE '"%' OR printer LIKE "'%"`. Executar **uma única vez** com guard (`SELECT COUNT(*) WHERE ...` antes/depois).
  - Adicionar **teste de regressão** em `backend/tests/test_parser.py` com a linha bruta capturada do `page_log` real (job ID 4 em `02-VERIFICATION.md`).
  - Coletar a linha bruta **antes** de codificar via `docker compose exec cups tail -n 50 /var/log/cups/page_log` para confirmar a hipótese (aspa no início vs aspa interna).
- **D-23:** **GAP-02-02 (username sem domínio AD) — NÃO bloquear Fase 3.**
  - **Investigação observacional primeiro** (não tocar em código antes de evidência):
    1. `docker compose exec cups tail -n 50 /var/log/cups/access_log` — formato do username recebido.
    2. `docker compose exec cups tail -n 50 /var/log/cups/page_log` — formato gravado.
    3. Em um PC Windows: `Get-PrintJob -PrinterName test_printer` durante envio para inspecionar `requesting-user-name` IPP.
  - Username continua **AS-IS** (preservar integridade forense/auditável) até evidência conclusiva.
  - Após investigação, **registrar conclusão como nova decisão** (D-XX no STATE.md) e atualizar/superseder D-14 Fase 2 se necessário.
  - **Sem normalização artificial** (não prefixar `DOMAIN\` no código se a evidência mostrar que CUPS não recebe).
  - Tarefa de investigação entra no plano da Fase 3 como **plano separado** (paralelizável às rotas) — não bloqueia entrega dos endpoints.

### E. Convenções da API + índices SQLite

- **D-24:** Prefixo de rotas: **`/api/v1/...`** (todas as rotas novas). Override do ROADMAP que listava paths raw (`/jobs`, `/stats/summary`, etc.) — versionamento explícito para evitar break-change futuro com Fase 4.
- **D-25:** Health endpoints — **manter `/healthz` existente** (sem prefixo, watcher status) e **adicionar `/api/v1/health` compatível** que retorne além do watcher também:
  - `db_reachable`: conseguiu `SELECT 1`.
  - `watcher_alive`: `_observer.is_alive()` (espelha `/healthz`).
  - `status`: `"ok"` se ambos true, `"degraded"` caso contrário (HTTP 200 mesmo degraded; HTTP 503 só se DB inacessível).
- **D-26:** **Swagger habilitado nesta fase** — `docs_url="/api/v1/docs"`, `openapi_url="/api/v1/openapi.json"`. Supersede D-12 Fase 2 que mantinha off intencional.
- **D-27:** **CORS via env var `ALLOWED_ORIGINS`** (comma-separated). Default no `.env.example`: `http://localhost:5173,http://VM_HOST`. **Sem wildcard `*`** mesmo no MVP. `CORSMiddleware` com `allow_credentials=False`, `allow_methods=["GET"]` (apenas GET na Fase 3), `allow_headers=["*"]`.
- **D-28:** **Sem autenticação** nesta fase (mantém PROJECT.md "Out of Scope"). Rede REDACTED_IP/16 é o controle de acesso.
- **D-29:** Índices SQLite criados via **migration idempotente** (`CREATE INDEX IF NOT EXISTS`) executada no startup (lifespan, antes do `purge_old_jobs`) — compatível com volume `db_data` já populado:
  - `idx_print_jobs_timestamp` ON `(timestamp DESC)`
  - `idx_print_jobs_username_timestamp` ON `(username, timestamp DESC)`
  - `idx_print_jobs_printer_timestamp` ON `(printer, timestamp DESC)`
  - `idx_print_jobs_job_id` ON `(job_id)`
  - **NÃO** criar `idx_print_jobs_job_group` agora (D-04 usa expressão `strftime` — index funcional adiciona complexidade sem benefício comprovado a 50k registros; reavaliar no profiling).

### F. Diretrizes arquiteturais transversais (MANDATÓRIO para o planner)

- **D-30:** **Estabilidade > abstração; legibilidade > genericismo.** Sem camadas "enterprise" sem necessidade real.
- **D-31:** **Reutilizar o `PrintJobRepository` existente** (`backend/app/db/repository.py`) — **NÃO criar uma segunda camada repository/repositories paralela**. Para leitura, preferir **services simples** (`app/services/jobs_service.py`, `app/services/stats_service.py`) que recebem `Session` e fazem queries SQLAlchemy explícitas.
- **D-32:** Pydantic schemas separados dos SQLAlchemy models — em `backend/app/api/schemas/` (ou `backend/app/schemas/`). Sem reaproveitar SQLAlchemy models como response model.
- **D-33:** Estrutura de rotas: `backend/app/api/v1/{jobs,stats,printers,health,export}.py`, agregadas em `backend/app/api/v1/__init__.py` com um único `APIRouter` montado em `main.py` via `app.include_router(api_v1_router, prefix="/api/v1")`.
- **D-34:** **Sem Celery, Redis, Postgres, SQLAlchemy async, FTS5, materialized views, XLSX, gunicorn**. Apenas o stack atual da Fase 2 + dependências necessárias para CSV/CORS.

### Claude's Discretion

- Nome exato do módulo de normalização (`app/services/normalization.py` vs função em `parser.py`).
- Layout exato de `backend/app/api/v1/` (1 arquivo por endpoint vs agrupados por recurso).
- Schema de paginação Pydantic (`PageResponse[T]` genérico vs schemas concretos por endpoint).
- Localização do script de backfill (`backend/migrations/2026-05-XX-fix-printer-quotes.sql` vs `backend/scripts/backfill_printer_quotes.py`).
- Detalhes de error handling: códigos HTTP exatos para inputs inválidos (date_from > date_to, size > 500, etc.) — convencional 422 (Pydantic) ou 400.
- Logging estruturado: manter `logging.basicConfig(level=INFO)` atual ou adicionar request ID via middleware leve.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requisitos e roadmap
- `.planning/PROJECT.md` — Stack (FastAPI + SQLAlchemy + SQLite), riscos AD username, Out-of-Scope (sem auth)
- `.planning/REQUIREMENTS.md` — EXPORT-01, EXPORT-02, DASH-06; herança CAPTURE-01–04, DATA-01–03, EXTEND-01–03
- `.planning/ROADMAP.md` Fase 3 — Goal, endpoints, success criteria (4 critérios mensuráveis)
- `.planning/STATE.md` — Decisões registradas (D-14 a revisar), GAPs abertos (GAP-02-01, GAP-02-02)

### Contexto de fases anteriores
- `.planning/phases/01-infrastructure-print-server/01-CONTEXT.md` — Rede REDACTED_IP/16, ACL CUPS, deploy
- `.planning/phases/02-log-pipeline-data-layer/02-CONTEXT.md` — D-01–D-17 Fase 2 (granularidade DB, NULL semântico, container backend mudo)
- `.planning/phases/02-log-pipeline-data-layer/02-VERIFICATION.md` — Evidência runtime do DB (linhas com aspa em printer, username sem domínio)
- `.planning/phases/02-log-pipeline-data-layer/02-PATTERNS.md` — Padrões de Dockerfile/entrypoint/services aplicáveis

### GAPs herdados (escopo desta fase)
- `.planning/todos/pending/GAP-02-01-parser-printer-quote.md` — Bug parser printer quote (D-22)
- `.planning/todos/pending/GAP-02-02-username-domain-ad.md` — Investigação username AD (D-23)

### Código existente a reutilizar
- `backend/app/main.py` — FastAPI app + lifespan (watcher + purge) + `/healthz`
- `backend/app/core/config.py` — Settings via env vars (estender com `ALLOWED_ORIGINS`)
- `backend/app/db/models.py` — `PrintJob`, `CaptureState`, `Policy`
- `backend/app/db/session.py` — `SessionLocal`, engine, `Base.metadata.create_all`
- `backend/app/db/repository.py` — `PrintJobRepository` (reutilizar; NÃO criar paralela — D-31)
- `backend/app/services/parser.py` — `PAGE_LOG_REGEX`, `parse_page_log_line` (corrigir GAP-02-01 aqui — D-22)
- `backend/app/services/retention.py` — Padrão de service simples com `Session` (modelo para `jobs_service`, `stats_service`)
- `backend/app/watcher/handler.py` — Hook `pre_process_job` (sem alteração nesta fase, EXTEND-03 OK)
- `backend/Dockerfile`, `backend/entrypoint.sh`, `backend/requirements.txt` — Container backend já provisionado
- `docker-compose.yml` — Serviço `backend` já existente (sem alteração estrutural; apenas `.env` ganha `ALLOWED_ORIGINS`)
- `.env.example` — Adicionar `ALLOWED_ORIGINS` (D-27) e possivelmente `API_TIMEZONE=America/Sao_Paulo` (D-10/D-20)

### Validação e checkpoint
- `scripts/validate-phase2.sh` — Modelo para `scripts/validate-phase3.sh` (mesmo padrão `--quick` + completo)
- `docker-compose.yml` portas — backend hoje sem `ports:`; **Fase 3 precisa expor** porta `8000` (decisão do planner — D-12 Fase 2 dizia "sem rotas REST públicas", agora é exatamente o oposto).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`PrintJobRepository.insert_job_idempotent`** + `on_conflict_do_nothing` — padrão idempotente já testado; usar `on_conflict_do_update` quando necessário no backfill.
- **`purge_old_jobs`** (`app/services/retention.py`) — modelo arquitetural de "service simples que recebe Session e SQLAlchemy core" (D-31). Replicar para `jobs_service`, `stats_service`.
- **FastAPI lifespan** (`main.py`) — já gerencia ciclo do `InotifyObserver`. Adicionar passo de **migration de índices** (D-29) ANTES do `purge_old_jobs` no `lifespan` startup.
- **`PAGE_LOG_REGEX`** (`parser.py`) — válido; só precisa do normalize wrapper (D-22).
- **`SessionLocal`** + `NullPool` — adequado para SQLite + FastAPI sync. Dependency injection FastAPI: criar `get_db()` dependency a partir de `app/db/session.py` (já existe contextmanager, falta versão para `Depends`).
- **`pytest` + `conftest.py`** — testes Fase 2 (24 passed) seguem padrão isolável; replicar em `backend/tests/test_api_*.py` usando `TestClient` do FastAPI.

### Established Patterns
- Decisões numeradas **D-NN por fase** (Fase 1 D-01–D-22, Fase 2 D-01–D-17, Fase 3 D-01–D-34).
- Validação Nyquist via `validate-phaseN.sh --quick` e suite completa.
- `.env.example` com placeholders seguros + comentários por fase (Fase 1 D-19, Fase 2 retention).
- Hostname/IP fixo `VM_HOST` para deploy real (Fase 1 D-17).
- Username AD baseline ainda inconclusivo (D-14 Fase 2 ↔ GAP-02-02 ativo).

### Integration Points
- **CUPS containerizado independente** — `/printers` NÃO consulta CUPS (D-21), evita acoplamento ao runtime.
- **Volume `db_data`** já populado — migrations de índice (D-29) e backfill (D-22) devem ser idempotentes e compatíveis com dados existentes.
- **Backend container precisa expor porta 8000** ao host para clientes locais (curl) e para a Fase 4 (nginx proxy futuro). Hoje `docker-compose.yml` não tem `ports:` no serviço `backend`.
- **`InotifyObserver` permanece** rodando em paralelo com as rotas — FastAPI sync handlers + watcher thread coexistem sem GIL bloqueio significativo para 20-100 users.

</code_context>

<specifics>
## Specific Ideas

- **Truncamento de timestamp por minuto** (`strftime('%Y-%m-%d %H:%M', timestamp)`) como chave de agregação — pragmático para SQLite, evita inventar coluna `job_signature` calculada.
- **Top-N por páginas, não por jobs** — alinha com o KPI real do negócio (volume de papel/toner) e com a Core Value do PROJECT.md.
- **DISTINCT printer no `/printers`** — backend não fala com CUPS, apenas com o histórico que ele já registrou. Mais simples + reflete realidade operacional.
- **Mês calendário (não rolling)** — coerente com fechamento contábil que o gestor (perfil "Gestor" em PROJECT.md) tipicamente espera.
- **CSV UTF-8 + BOM + `;`** — combinação testada para Excel Windows pt-BR sem prompt de import.
- **`StreamingResponse` com 100k cap** — equilíbrio entre não-explodir-memória e UX previsível para o admin de TI.
- **Investigação GAP-02-02 ANTES do código** — coletar `access_log`, `page_log` bruto, `Get-PrintJob` IPP — evita decisão precipitada sobre normalização.
- **Estrutura preparada para `granularity=page` futura** sem expor agora — option door que o planner deve manter aberta.

</specifics>

<deferred>
## Deferred Ideas

- **Materialized view / coluna `job_signature` calculada** — não justificada a 50k. Reavaliar se `EXPLAIN QUERY PLAN` mostrar full scan na agregação.
- **FTS5** para busca por `job_name` — fora da Fase 3 (LIKE é suficiente para 50k). Considerar se busca virar bottleneck na Fase 4.
- **XLSX nativo** — Fase 4+ se admin pedir formatação rica. CSV cobre EXPORT-01/EXPORT-02 do MVP.
- **Status online/offline em `/printers`** — Fase 5 SERVER-04 (interface de cadastro + status).
- **Polling CUPS via IPP/lpstat** — só faz sentido junto com SERVER-04.
- **Autenticação no dashboard** — v2 (`REQUIREMENTS.md` Out of Scope MVP).
- **Políticas de bloqueio ativas** (hook `pre_process_job` retornando `False`) — v2.
- **API REST pública para integrações externas** — v2 (`REQUIREMENTS.md` v2).
- **Endpoints PATCH/DELETE em `/jobs`** — não solicitados; jobs são imutáveis no MVP (auditabilidade).
- **Rate limiting / paginação cursor-based** — não justificado para 20-100 users em rede local.
- **OpenTelemetry / tracing distribuído** — overkill para single container backend.
- **Async SQLAlchemy** — `NullPool` + sync handlers + watcher em thread separada é suficiente.

</deferred>

---

*Phase: 3-Backend API*
*Context gathered: 2026-05-26*
