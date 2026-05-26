---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: in_progress
last_updated: "2026-05-26T20:10:00.000Z"
progress:
  total_phases: 5
  completed_phases: 2
  total_plans: 10
  completed_plans: 10
  percent: 40
gaps_open: 2
---

# STATE — PrintWatch

**Última atualização:** 2026-05-26  
**Fase atual:** Fase 2 completa (functional with known data-quality gaps) — próxima: Fase 3 (Backend API)

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
| Próxima ação | `/gsd-discuss-phase 3` — Backend API |

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
| 3 | Backend API | Pendente |
| 4 | Dashboard Web | Pendente |
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
- **2026-05-26:** Username IPP Windows registra como `DOMAIN\usuario` no page_log — formato D-14 válido
- **2026-05-26:** TailReader state_repo usa get()/upsert(inode, byte_offset) — CheckpointRepository no Plano 03
- **2026-05-26:** Parser retorna None para linhas fora do PAGE_LOG_REGEX (nunca propaga ao banco)
- **2026-05-26:** Pipeline end-to-end: InotifyObserver em /var/log/cups + filtro page_log + INSERT idempotente
- **2026-05-26:** /healthz expõe watcher alive para probe Docker (exceção D-12)
- **2026-05-26:** purge_old_jobs no lifespan com cutoff UTC; LOG_RETENTION_DAYS default 90
- **2026-05-26:** logging.basicConfig(INFO) para logs de purge/watcher no docker compose
- **2026-05-26:** Fase 2 aprovada (functional with known data-quality gaps): GAP-02-01 (parser printer quote) e GAP-02-02 (username sem domínio AD) registrados para resolver na Fase 3
- **2026-05-26:** D-14 (`DOMAIN\usuario` no page_log) marcada para revisão — evidência atual mostra `user.example` sem domínio; investigar antes de alterar parser
- **2026-05-26:** Incidente Windows Internet Print Provider (porta órfã `0x0000000d`) — não é bug do projeto, é estado local; runbook de troubleshooting na Fase 5

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

| ID | Tipo | Resolve em | Descrição |
|----|------|-----------|-----------|
| GAP-02-01 | bug | Fase 3 | Parser captura aspa inicial em `printer` |
| GAP-02-02 | investigation | Fase 3 | Username sem domínio AD — investigar antes de mudar código |

## Session Continuity

Last session: 2026-05-26T20:10:00.000Z
Stopped at: Fase 2 aprovada com gaps; pronto para `/gsd-discuss-phase 3`
Resume file: .planning/phases/02-log-pipeline-data-layer/02-VERIFICATION.md
