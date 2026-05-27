# PrintWatch — Project Context

**Versão:** 1.5 (planejamento)  
**Milestone ativa:** v1.5 Management Platform  
**Última milestone shipped:** v1.0 Audit Platform — 2026-05-27  
**Status:** Brownfield — evoluindo de auditoria para gestão operacional

---

## What This Is

PrintWatch é um sistema self-hosted de **auditoria e gestão de impressão**. Atua como print server intermediário (CUPS): jobs passam pela VM, são registrados em SQLite e expostos via API e dashboards na rede local.

**Core Value (v1.0 — entregue):** Registrar 100% dos jobs com rastreabilidade (quem, o quê, quando, quantas páginas) sem interromper a impressão física.

**Core Value (v1.5 — ativo):** Transformar logs em **gestão operacional** — cadastro de impressoras e organização, custos por página, chargeback interno, analytics gerencial e saúde da frota — experiência PaperCut-like sem paridade enterprise.

---

## Current Milestone: v1.5 Management Platform

**Goal:** Evoluir de plataforma de auditoria para plataforma de gestão operacional de impressão, preservando monólito, SQLite, Docker Compose e pipeline append-only que nunca bloqueia impressão.

**Target features:**
- Cadastro formal de impressoras (inventário, metadados, vínculo fila CUPS)
- Departamentos, usuários e centros de custo (entidades distintas)
- Import CSV de organização (antes de LDAP)
- Tarifas mono/color, custo por job, chargeback interno (relatórios/CSV)
- Dashboard gerencial (consumo, tops, comparativos)
- Fleet: status online/offline (CUPS/IPP primário, ping IP fallback)
- Toner: telemetria SNMP opt-in (sem controle de estoque)
- UI de configuração (Settings) complementando dashboard de auditoria

**Diretrizes arquiteturais (v1.5):**
- SQLite + monólito + Docker Compose — sem microserviços
- Cadastro e analytics **não podem impactar** captura de jobs (watcher isolado)
- Pipeline append-only; falhas em settings/analytics não bloqueiam impressão
- CC ≠ departamento; chargeback = alocação interna, não faturamento contábil
- Inventário = impressoras; toner = monitoramento apenas

---

## Current State (v1.0 shipped)

| Camada | Estado |
|--------|--------|
| CUPS | Print server IPP na rede; `page_log` configurado |
| Captura | Watcher inotify + parser + SQLite (1 linha/página) |
| API | FastAPI `/api/v1` — jobs, stats, export CSV, health |
| Frontend | React + Vite + Tailwind; nginx :80 |
| Deploy | Docker Compose (cups + backend + nginx) |
| Validação | VM real; jobs Windows; checkpoint humano aprovado |

**Schema atual:** `print_jobs`, `capture_state`, `policies` — sem FKs de organização.

**Dívida aceita:** `/printers` = DISTINCT do log; username AS-IS do CUPS; retenção default 90 dias via env.

---

## Contexto do Ambiente

| Atributo | Valor |
|----------|-------|
| Rede local | REDACTED_IP/16 |
| Usuários estimados | 20–100 |
| Impressoras | HP e Samsung, IP na rede |
| Domínio Windows | AD ativo; username via IPP (formato variável) |
| Hypervisor | XCP-ng |
| Servidor | VM Ubuntu 22.04 LTS |
| Clientes | Windows 10/11 via IPP → VM |

---

## Requirements

Ver `.planning/REQUIREMENTS.md` (milestone v1.5). Resumo:

### Validated (v1.0)

- ✓ CAPTURE, SERVER-01–03, DATA, EXPORT, DASH, DEPLOY-01–02, EXTEND — Fases 1–4

### Active (v1.5)

- Fase 5: Master Data & Organization (ORG, INV, IMPORT, SETTINGS, DATA-04+)
- Fase 6: Costing & Chargeback (COST, CHRG)
- Fase 7: Manager Analytics (ANAL)
- Fase 8: Fleet Health & Toner (FLEET, TONER)

### Out of Scope (v1.5)

| Item | Razão |
|------|-------|
| Autenticação dashboard | v3.0 ou nginx basic auth |
| Cotas e bloqueio ativo | v2.5+ Policy |
| LDAP/AD sync | Após master data manual estável |
| PostgreSQL | Só com evidência de escala |
| Faturamento/billing contábil | Chargeback = relatório interno apenas |
| Estoque de toner/consumíveis | Toner = telemetria SNMP opt-in |
| Microserviços / message bus | Contradiz princípios |
| Multi-site, app mobile | Futuro |
| Paridade PaperCut enterprise | Subset pragmático |
| DEPLOY-03/04 | v3.0 Production |

---

## Stack Tecnológica

| Camada | Tecnologia |
|--------|-----------|
| Print Server | CUPS 2.4+ |
| Log Watcher | Python 3 + watchdog |
| Banco | SQLite (SQLAlchemy + Alembic) |
| Backend | FastAPI |
| Frontend | React + Vite + TailwindCSS v4 |
| Fleet/Toner | IPP/CUPS + ping + pysnmp (opt-in) |
| Deploy | Docker Compose + nginx |

---

## Usuários

| Perfil | v1.0 | v1.5 |
|--------|------|------|
| Admin TI | Histórico, filtros, CSV | + Settings, cadastro, import |
| Gestor | — | Dashboard gerencial, custos |
| Usuário final | Transparente | Transparente |

---

## Key Decisions

| Decisão | Resultado |
|---------|-----------|
| Linux/CUPS vs Windows Server | ✓ CUPS na VM dedicada |
| SQLite vs PostgreSQL | ✓ SQLite v1.0–v1.5 |
| 1 linha/página na ingestão | ✓ Agregação na API |
| Username AS-IS | ✓ GAP-02-02 fechado |
| CC separado de Department | ✓ v1.5 — nem todo dept é CC contábil |
| Chargeback interno apenas | ✓ CSV/relatórios, sem fatura |
| Fleet: CUPS/IPP → ping → SNMP toner | ✓ v1.5 híbrido simples |
| Master data antes de costing/analytics | ✓ Fase 5 primeiro |

---

## Evolution

Este documento evolui em transições de fase e limites de milestone.

**Após cada fase** (`/gsd-transition`): requisitos validados → Validated; novos → Active; decisões → Key Decisions.

**Após cada milestone** (`/gsd-complete-milestone`): revisão completa; Core Value; Out of Scope.

---

<details>
<summary>Histórico v1.0 (Maio 2026)</summary>

MVP substituindo PaperCut em PME. Fases 1–4 = Audit Platform. Artefatos: `.planning/milestones/v1.0-*`.

</details>

---
*Last updated: 2026-05-27 — milestone v1.5 initialized*
