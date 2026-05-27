---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: Ready to execute
last_updated: "2026-05-27T13:30:22.160Z"
progress:
  total_phases: 4
  completed_phases: 2
  total_plans: 23
  completed_plans: 10
  percent: 43
---

# STATE — PrintWatch

**Última atualização:** 2026-05-27  
**Fase atual:** Fase 4 (Dashboard Web) — planejada; pronta para execução

---

## Status do Projeto

| Item | Status |
|------|--------|
| Fase 1 Plan 01 | ✓ Scaffold deploy |
| Fase 1 Plan 02 | ✓ Container CUPS |
| Fase 1 Plan 03 | ✓ setup-printer + VM docs |
| Fase 1 Plan 04 | ✓ Validação E2E (local + IPP remoto) |
| Fase 1 Plan 05 | ✓ Deploy VM VM_HOST |
| Fase 2 Plan 01 | ✓ Backend + SQLite |
| Fase 2 Plan 02 | ✓ Parser + TailReader TDD |
| Fase 2 Plan 03 | ✓ Repository + watcher pipeline |
| Fase 2 Plan 04 | ✓ Retention purge no startup |
| Fase 2 Plan 05 | ✓ validate-phase2 + checkpoint humano (aprovado 2026-05-26) |
| Fase 3 Discussão | ✓ Contexto capturado (`03-CONTEXT.md` + `03-DISCUSSION-LOG.md`) — 2026-05-26 |
| Fase 3 Pesquisa | ✓ `03-RESEARCH.md` (FastAPI 0.136 + SQLAlchemy 2.0 + Pydantic 2.13 via context7 MCP) — 2026-05-26 |
| Fase 3 Planejamento | ✓ 6 plans em 3 waves (`03-01..03-06-PLAN.md`) — 2026-05-26 |
| Fase 3 execução | Wave 1–2 concluídas; `validate-phase3.sh --quick` OK na VM; GAP-02-02 investigado e fechado (03-06) |
| Fase 4 Discussão | ✓ Contexto capturado (`04-CONTEXT.md` + `04-DISCUSSION-LOG.md`) — 2026-05-27 |
| Fase 4 UI-SPEC | ✓ `04-UI-SPEC.md` aprovado (6/6 dimensões) — 2026-05-27 |
| Fase 4 Planejamento | ✓ 6 plans em 3 waves (`04-01..04-06-PLAN.md`) — 2026-05-27 |
| Próxima ação | `/gsd-execute-phase 4` |

---

## Bloqueio resolvido

**ID:** B-01-04-VM — **resolvido 2026-05-26**  
**Evidência:** CUPS em VM_HOST, porta 631, test_printer enabled, validate --quick 17 PASS na VM.

---

## Fases

| # | Nome | Status |
|---|------|--------|
| 1 | Infrastructure & Print Server | ✓ Completa (5/5 plans) |
| 2 | Log Pipeline & Data Layer | ✓ Completa (5/5 plans) — functional with known data-quality gaps |
| 3 | Backend API | Planejada — 6 plans em 3 waves (Wave 1: 01 infra + 02 GAP-01; Wave 2: 03 jobs/printers/health + 04 stats + 05 export csv; Wave 3: 06 validate + GAP-02) |
| 4 | Dashboard Web | Discussão ✓ + UI-SPEC ✓ — pronto para planejar |
| 5 | Client Config & Hardening | Pendente |

---

## Decisões Registradas

- Plataforma: Ubuntu 22.04 LTS em VM XCP-ng (descartado Windows Server)
- Stack: CUPS + Python + FastAPI + React + SQLite + Docker Compose
- Modo: YOLO (auto-aprovação), Paralelo, Budget (modelos)
- Granularidade: Standard (5–8 fases)
- ALLOWED_NETWORK fixo em REDACTED_IP/16 — sem ranges RFC1918 genéricos da SPEC (D-06)
- ACL CUPS inclui @LOCAL para healthcheck interno além de ALLOWED_NETWORK
- validate-phase1.sh WARN quando Docker offline — não FAIL
- Fallback cups-pdf usa PPD lsb/usr/cups-pdf/CUPS-PDF_noopt.ppd
- setup-printer detecta placeholder URI e aplica fallback automaticamente
- **2026-05-26:** Deploy VM real (01-05) é pré-requisito explícito antes de validação IPP remota (01-04 Task 3)
- **2026-05-26:** VM printwatch operacional — preferir Docker CE existente sobre apt docker.io (conflito containerd)
- **2026-05-26:** TEST_PRINTER_URI backend deve usar porta :631 (`ipp://host:631/ipp/print`) para impressão física HP/Samsung
- **2026-05-26 → 2026-05-27:** D-14 revisada (Fase 3 plan 06) — jobs IPP Windows atuais chegam ao `page_log` como `user.example` **sem** prefixo `DOMAIN\`; parser persiste AS-IS; **não** concatenar domínio artificialmente; 53 jobs históricos com `DOMAIN\user.example` preservados no SQLite; enriquecimento LDAP/AD = v2
- **2026-05-26:** TailReader state_repo usa get()/upsert(inode, byte_offset) — CheckpointRepository no Plano 03
- **2026-05-26:** Parser retorna None para linhas fora do PAGE_LOG_REGEX (nunca propaga ao banco)
- **2026-05-26:** Pipeline end-to-end: InotifyObserver em /var/log/cups + filtro page_log + INSERT idempotente
- **2026-05-26:** /healthz expõe watcher alive para probe Docker (exceção D-12)
- **2026-05-26:** purge_old_jobs no lifespan com cutoff UTC; LOG_RETENTION_DAYS default 90
- **2026-05-26:** logging.basicConfig(INFO) para logs de purge/watcher no docker compose
- **2026-05-26:** Fase 2 aprovada (functional with known data-quality gaps): GAP-02-01 (parser printer quote) e GAP-02-02 (username sem domínio AD) registrados para resolver na Fase 3
- **2026-05-27 (Fase 3 plan 06):** GAP-02-02 fechado — classificação (a); recomendação (1); evidência em `03-INVESTIGATION-username-ad.md`
- **2026-05-26:** Incidente Windows Internet Print Provider (porta órfã `0x0000000d`) — não é bug do projeto, é estado local; runbook de troubleshooting na Fase 5
- **2026-05-26 (Fase 3 discuss):** API agregada **por job** (não por página); chave de agregação `(printer_normalized, job_id, username, job_name, strftime('%Y-%m-%d %H:%M', timestamp))`; `pages = COUNT(*)`
- **2026-05-26 (Fase 3 discuss):** Banco em **UTC**, API converte para **America/Sao_Paulo** apenas na serialização e na interpretação de `date_from`/`date_to`
- **2026-05-26 (Fase 3 discuss):** CSV em **UTF-8 com BOM**, separador `;`, cabeçalhos pt-BR, `StreamingResponse`, cap 100k linhas
- **2026-05-26 (Fase 3 discuss):** `/stats/summary` — "hoje"/"mês" em **calendário local** America/Sao_Paulo; top usuários/impressoras **por total de páginas** (default top=5); janelas hoje+mês+total
- **2026-05-26 (Fase 3 discuss):** `/printers` via `DISTINCT printer FROM print_jobs` — sem acoplamento com runtime CUPS (online/offline → Fase 5 SERVER-04)
- **2026-05-26 (Fase 3 discuss):** Prefixo de rotas **`/api/v1/*`** (versionado); Swagger habilitado em `/api/v1/docs`; CORS via env `ALLOWED_ORIGINS` (sem wildcard); manter `/healthz` e adicionar `/api/v1/health` com `db_reachable`+`watcher_alive`
- **2026-05-26 (Fase 3 discuss):** GAP-02-01 **corrigir agora** — `normalize_printer_name()` no parser + backfill idempotente no SQLite + teste regressão
- **2026-05-26 (Fase 3 discuss):** GAP-02-02 **investigação observacional primeiro** — coletar `access_log`, `page_log` bruto, `Get-PrintJob` IPP Windows; username AS-IS até evidência conclusiva; não bloqueia Fase 3
- **2026-05-26 (Fase 3 discuss):** Índices SQLite via migration idempotente no `lifespan` startup (`CREATE INDEX IF NOT EXISTS`): `timestamp`, `(username, timestamp)`, `(printer, timestamp)`, `(job_id)` — sem índice funcional sobre `strftime` ainda
- **2026-05-26 (Fase 3 discuss):** Reutilizar `PrintJobRepository` existente — **NÃO** criar segunda camada repository paralela; services simples + queries SQLAlchemy explícitas (modelo `app/services/retention.py`)
- **2026-05-26 (Fase 3 plan):** Estrutura final: 6 plans em 3 waves; Wave 1 paralela = infra rotas (01) + GAP-02-01 (02); Wave 2 paralela = jobs/printers/health (03) + stats (04) + export csv (05); Wave 3 sequencial = validate-phase3 + investigação GAP-02-02 (06)
- **2026-05-26 (Fase 3 plan):** Sem deps novas em requirements.txt — FastAPI 0.136.3 + SQLAlchemy 2.0.50 + Pydantic 2.13.4 cobrem CORS, StreamingResponse, Generic[T], yield_per nativamente; CSV é escrita manual (sem pandas)
- **2026-05-27 (Fase 4 discuss):** Visual Apple HIG + acento PaperCut `#00AE5B`; cards = jobs/páginas hoje + top mês (`mes.top_*[0]` com "Nome — N páginas"); presets Hoje/7d/Mês + date custom; impressora = dropdown `/printers` exato; tabela ~40px semi-compact; nginx :80 nesta fase; `formatMediaLabel` mapa local; stack React+Vite+TS+Tailwind+TanStack Query; sem charts/auth/TLS/websocket

## Performance Metrics

| Phase-Plan | Duration | Tasks | Files |
|------------|----------|-------|-------|
| 01-01 | 8min | 3 | 3 |
| 01-02 | 18min | 3 | 5 |
| 01-03 | 28min | 3 | 5 |
| 01-04 | 45min | 3 | 3 |
| 01-05 | 25min | 3 | 4 |
| 02-01 | 18min | 2 | 14 |
| 02-02 | 12min | 2 | 9 |
| 02-03 | 22min | 2 | 7 |
| 02-04 | 18min | 2 | 3 |
| 02-05 | 25min | 2 | 1 + checkpoint humano (aprovado) |

## Gaps Abertos

Nenhum gap aberto (`gaps_open: 0`).

| ID | Status | Resolvido em |
|----|--------|--------------|
| GAP-02-01 | ✓ resolved | 03-02 (`normalize_printer_name` + backfill) |
| GAP-02-02 | ✓ resolved | 03-06 (investigação observacional; username AS-IS) |

## Session Continuity

Last session: 2026-05-27T12:00:00.000Z
Stopped at: Phase 4 UI-SPEC approved
Resume file: .planning/phases/04-dashboard-web/04-UI-SPEC.md
