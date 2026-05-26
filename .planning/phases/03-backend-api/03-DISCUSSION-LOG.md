# Phase 3: Backend API - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-26
**Phase:** 03-backend-api
**Areas discussed:** A (jobs/paginação/filtros), B (CSV), C (stats + printers), D (GAPs Fase 2), E (convenções API + índices)

---

## A — Forma de `/jobs` + paginação + filtros + ordenação

| Opção | Descrição | Selecionado |
|-------|-----------|-------------|
| Agregado por job | API expõe 1 linha por job (agregação SQL sobre páginas) | ✓ |
| 1 linha por página | API espelha o banco diretamente | |
| Híbrido `?granularity=` | Expor ambos via query param | parcial (estrutura preparada, query param NÃO exposto agora — D-19) |
| Paginação `page/size` (50 default, 500 max) | Convencional, simples | ✓ |
| Paginação cursor-based | Mais eficiente para datasets enormes | (não justificado a 50k) |
| `username` exact match | Filtro estrito | |
| `username` contains case-insensitive | Match flexível | ✓ |
| `printer` exact match | Estrito | ✓ |
| `printer` contains | Flexível | |
| `search` LIKE `%term%` no `job_name` | Sem dependência extra | ✓ |
| `search` FTS5 SQLite | Full-text índice | (deferido — só se LIKE virar bottleneck) |
| `date_from`/`date_to` inclusivos | Semântica intuitiva | ✓ |
| Timezone UTC end-to-end | Sem conversão | |
| Timezone UTC no banco + America/Sao_Paulo na API | Conversão na camada API | ✓ |
| Ordem `timestamp DESC` default | Recentes primeiro | ✓ |

**User's choice:** Agregado por job + page/size + contains/exact mix conforme tabela.

**Notes:**
- `timestamp_window` truncado por minuto (`strftime('%Y-%m-%d %H:%M', timestamp)`) como chave de agregação — pragmático para SQLite, evita criar coluna calculada.
- `pages = COUNT(*)` por grupo (1 linha = 1 página no banco).
- `pages = COUNT(*)` por grupo (1 linha = 1 página no banco).
- Timestamp do job agregado = `MIN(timestamp)` do grupo.
- Persistência intocada (D-01 Fase 2 preservada).

---

## B — Exportação CSV (`/export/csv`)

| Opção | Descrição | Selecionado |
|-------|-----------|-------------|
| Mesmo dataset agregado da `/jobs` | Consistência API ↔ CSV | ✓ |
| Dataset granular (1 linha por página) | Detalhe forense | (preparado internamente, não exposto — D-19) |
| UTF-8 puro | Padrão moderno | |
| UTF-8 com BOM | Compatível Excel Windows pt-BR | ✓ |
| Separador `,` (padrão internacional) | RFC 4180 | |
| Separador `;` (Excel pt-BR default) | Abre direto no Excel BR | ✓ |
| Cabeçalhos em en (`timestamp, username, ...`) | Convencional API | |
| Cabeçalhos em pt-BR (`Data/Hora, Usuário, ...`) | Amigável para o admin | ✓ |
| In-memory CSV completo | Simples | |
| `StreamingResponse` linha a linha | Escala melhor | ✓ |
| Limite 100k linhas | Hard cap previsível | ✓ |
| Sem limite | Risco de OOM | |
| XLSX nativo | Formatação rica | (deferido) |

**User's choice:** Dataset agregado da `/jobs`; UTF-8 + BOM; `;`; cabeçalhos pt-BR; streaming; cap 100k.

**Notes:**
- Filename: `print_jobs_YYYYMMDD_HHMM.csv` (timestamp local America/Sao_Paulo).
- Se exceder 100k, retornar 400 com mensagem orientando refinar filtros.
- Estrutura interna deve suportar `granularity=page|job` futura sem refactor — query param não exposto agora.

---

## C — `/stats/summary` + `/printers`

| Opção | Descrição | Selecionado |
|-------|-----------|-------------|
| Timezone UTC para "hoje"/"mês" | Sem conversão | |
| Timezone America/Sao_Paulo | Alinha com a operação local | ✓ |
| "Hoje" = janela 24h rolling | Móvel | |
| "Hoje" = dia calendário local | Fechamento intuitivo | ✓ |
| "Mês" = últimos 30d (rolling) | Móvel | |
| "Mês" = mês calendário corrente | Coerente com fechamento contábil | ✓ |
| Top usuários por número de jobs | Cada job conta = 1 | |
| Top usuários por total de páginas | KPI real (papel/toner) | ✓ |
| Top impressoras por número de jobs | | |
| Top impressoras por total de páginas | Mesmo critério dos users | ✓ |
| Default `top=5` | Convencional | ✓ |
| Janelas: hoje, mês, total | Cobertura completa | ✓ |
| `/printers` ← `DISTINCT printer FROM print_jobs` | Sem acoplamento com CUPS | ✓ |
| `/printers` ← `lpstat -p` via docker exec | Status em tempo real | |
| `/printers` ← IPP `CUPS-Get-Printers` | Standard IPP | |
| Online/offline aqui | Funcionalidade rica | (Fase 5 SERVER-04) |

**User's choice:** America/Sao_Paulo; dia/mês calendário; top por páginas; default 5; janelas hoje+mês+total; `/printers` via DISTINCT do banco; sem online/offline na Fase 3.

**Notes:**
- Schema sugerido com `hoje`, `mes`, `total` cada um expondo `jobs`, `pages`, `top_users`, `top_printers`.
- `/printers` é endpoint informacional/histórico nesta fase, evita coupling com runtime CUPS.

---

## D — GAPs Fase 2

| Opção | Descrição | Selecionado |
|-------|-----------|-------------|
| GAP-02-01 — fix só daqui pra frente | Não tocar dados existentes | |
| GAP-02-01 — fix parser + backfill DB | Limpa dados retroativamente | ✓ |
| GAP-02-01 — strip de aspas em todos os campos string | Genérico | (parcial — só `printer` confirmado; outros campos `null_if_dash` mantém) |
| GAP-02-01 — função `normalize_printer_name` dedicada | Idempotente, testável | ✓ |
| GAP-02-02 — assumir bug no parser e prefixar `DOMAIN\` | Reescrever evidência | |
| GAP-02-02 — investigação observacional primeiro | Coletar evidência antes de código | ✓ |
| GAP-02-02 — bloquear endpoints até resolver | Sequencial | |
| GAP-02-02 — paralelo aos endpoints | Não bloqueia entrega | ✓ |

**User's choice:** GAP-02-01 corrigir AGORA (parser + backfill idempotente + teste regressão). GAP-02-02 investigação observacional primeiro, sem bloquear Fase 3.

**Notes:**
- Coletar linha bruta do `page_log` ANTES de codificar o fix (confirmar hipótese sobre origem da aspa).
- Backfill como script/migration explícito em `backend/migrations/` ou `backend/scripts/`, idempotente.
- Para GAP-02-02 coletar: `access_log`, `page_log` bruto, `Get-PrintJob` no Windows IPP.
- Username permanece AS-IS até evidência conclusiva; sem normalização artificial.
- Investigação como plano separado, paralelizável às rotas.

---

## E — Convenções de API + índices SQLite

| Opção | Descrição | Selecionado |
|-------|-----------|-------------|
| Prefixo `/jobs` raw (como ROADMAP) | Mais curto | |
| Prefixo `/api/v1/*` | Versionado, futuro-proof | ✓ |
| Manter Swagger off (D-12 Fase 2) | Conservador | |
| Habilitar Swagger nesta fase (`/api/v1/docs`) | Documentação automática | ✓ |
| CORS wildcard `*` | Permissivo no MVP local | |
| CORS via env `ALLOWED_ORIGINS` | Controlado | ✓ |
| `/health` substitui `/healthz` | Renomeio único | |
| Manter `/healthz` + adicionar `/api/v1/health` | Compatibilidade + nova capacidade | ✓ |
| Autenticação básica nesta fase | Conservadora | |
| Sem autenticação (firewall) | MVP local | ✓ |
| Sem índices (confiar no SQLite default) | | |
| Índices nas colunas críticas (timestamp, username, printer, job_id) | Atende DASH-06 | ✓ |
| Migration de índices no startup (idempotente) | Compatível com `db_data` populado | ✓ |
| Recriar DB do zero | Destrutivo | |

**User's choice:** `/api/v1/*`; Swagger ON; CORS via env; manter `/healthz` + adicionar `/api/v1/health`; sem auth; índices via migration idempotente no startup.

**Notes:**
- `/api/v1/health` retorna `db_reachable` + `watcher_alive` + `status` ("ok"|"degraded"); 503 só se DB inacessível.
- CORS: `allow_credentials=False`, `allow_methods=["GET"]`, default `ALLOWED_ORIGINS=http://localhost:5173,http://VM_HOST`.
- Índices: `timestamp`, `(username, timestamp)`, `(printer, timestamp)`, `(job_id)`. NÃO criar índice funcional sobre `strftime` ainda.
- Migration no `lifespan` startup, ANTES do `purge_old_jobs`.

---

## Diretrizes arquiteturais transversais (capturadas durante a discussão)

- Estabilidade > abstração; legibilidade > genericismo.
- **Reutilizar** `PrintJobRepository` existente — **NÃO** criar segunda camada repository paralela.
- Services simples + queries SQLAlchemy explícitas (modelo: `app/services/retention.py`).
- Pydantic schemas separados dos SQLAlchemy models.
- Sem Celery / Redis / Postgres / SQLAlchemy async / FTS5 / materialized views / XLSX / gunicorn.
- Plano de execução **incremental** com commits atômicos por capacidade.
- Checkpoints de validação manual (curl + smoke tests).
- Riscos/performance notes para 50k+ — incluir `EXPLAIN QUERY PLAN` nas queries principais.
- Abordagem brownfield-friendly (DB já populado, watcher já rodando).

## Claude's Discretion

- Nome do módulo de normalização (`app/services/normalization.py` vs função em `parser.py`).
- Layout exato de `backend/app/api/v1/` (1 arquivo por endpoint vs agrupados).
- Schema de paginação Pydantic (`PageResponse[T]` genérico vs concretos).
- Localização do script de backfill (`backend/migrations/*.sql` vs `backend/scripts/*.py`).
- Códigos HTTP exatos para inputs inválidos (400 vs 422).
- Logging estruturado vs `logging.basicConfig` atual.

## Deferred Ideas

- Materialized view / coluna `job_signature` calculada — reavaliar se EXPLAIN mostrar full scan.
- FTS5 para `job_name`.
- XLSX nativo.
- `/printers` online/offline + polling CUPS — Fase 5 SERVER-04.
- Autenticação no dashboard.
- Políticas de bloqueio ativas (hook `pre_process_job` False).
- API REST pública externa.
- PATCH/DELETE em `/jobs` (jobs imutáveis no MVP).
- Rate limiting / paginação cursor-based.
- OpenTelemetry / tracing.
- Async SQLAlchemy.
