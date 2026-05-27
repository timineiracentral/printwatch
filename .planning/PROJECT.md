# PrintWatch — Project Context

**Versão:** 1.5 (em planejamento)  
**Última milestone:** v1.0 Audit Platform — shipped 2026-05-27  
**Status:** Brownfield — plataforma de auditoria operacional; evoluindo para gestão

---

## What This Is

PrintWatch é um sistema self-hosted de **auditoria e gestão de impressão**. Atua como print server intermediário (CUPS): jobs passam pela VM, são registrados em SQLite e expostos via API e dashboard na rede local.

**Core Value (v1.0 — entregue):** Registrar 100% dos jobs com rastreabilidade (quem, o quê, quando, quantas páginas) sem interromper a impressão física.

**Core Value (v1.5 — próximo):** Transformar logs em **gestão operacional** — impressoras e departamentos cadastrados, custos por página, visão gerencial de consumo.

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

**Arquitetura:** Monólito brownfield em Docker Compose. SQLite adequado para 20–100 usuários. Sem auth no dashboard (rede local).

**Dívida aceita:** Username sem prefixo AD via IPP; `/printers` = DISTINCT do log (sem inventário); retenção default 90 dias via env.

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

### Validated (v1.0)

- ✓ Captura completa de jobs (CAPTURE-01–04) — Fases 1–2
- ✓ CUPS + deploy Compose (SERVER-01–03, DEPLOY-01–02) — Fase 1
- ✓ Persistência e retenção (DATA-01–03) — Fase 2
- ✓ API REST com filtros, stats, CSV (EXPORT, DASH-06) — Fase 3
- ✓ Dashboard web com filtros e export (DASH-01–06) — Fase 4
- ✓ Extensibilidade schema (EXTEND-01–03) — Fase 2
- ✓ Impressão física independente do backend (CAPTURE-04)

### Active (v1.5 — a definir via `/gsd-new-milestone`)

- [ ] Cadastro formal de impressoras (inventário, metadados, vínculo CUPS)
- [ ] Departamentos e associação usuário → departamento
- [ ] Custos por página mono/color e relatórios por departamento
- [ ] Dashboard gerencial (consumo, tops, comparativos)
- [ ] Status online/offline de impressoras
- [ ] Monitoramento de toner (SNMP, opt-in)
- [ ] Import CSV de usuários/departamentos (antes de LDAP)

### Out of Scope (atualizado)

| Item | Razão |
|------|-------|
| Autenticação dashboard | v3.0 ou rede + nginx basic auth |
| Cotas e bloqueio ativo | v2.5+ Policy context |
| LDAP/AD sync | Após master data manual estável |
| PostgreSQL | Só com evidência de escala |
| Multi-site | Ambiente único |
| App mobile | Perfil admin browser |
| API pública externa | Integrações futuras |
| Paridade PaperCut completa | Subset pragmático |

---

## Stack Tecnológica

| Camada | Tecnologia |
|--------|-----------|
| Print Server | CUPS 2.4+ |
| Log Watcher | Python 3 + watchdog |
| Banco | SQLite (SQLAlchemy) |
| Backend | FastAPI |
| Frontend | React + Vite + TailwindCSS v4 |
| Deploy | Docker Compose + nginx |

---

## Usuários

| Perfil | v1.0 | v1.5+ |
|--------|------|-------|
| Admin TI | Histórico, filtros, CSV | + cadastro impressoras/org |
| Gestor | — | Dashboard consumo/custo |
| Usuário final | Transparente | Transparente |

---

## Key Decisions

| Decisão | Resultado |
|---------|-----------|
| Linux/CUPS vs Windows Server | ✓ CUPS na VM dedicada |
| SQLite vs PostgreSQL | ✓ SQLite v1.0–v1.5 |
| 1 linha/página na ingestão | ✓ Agregação na API |
| Username AS-IS (sem domínio artificial) | ✓ GAP-02-02 fechado |
| Milestone v1.0 = Fases 1–4 apenas | ✓ Fase 5 antiga descontinuada |
| Próxima milestone v1.5 Management | ✓ Master data antes de hardening |

---

## Next Milestone Goals (v1.5)

1. Entidades de domínio: `printers`, `departments`, `users`, `cost_rates`
2. APIs e UI de configuração (settings)
3. Custo e analytics por departamento/usuário
4. Base para fleet health (sem overengineering)

**Comando:** `/gsd-new-milestone`

---

<details>
<summary>Histórico v1.0 (inicialização Maio 2026)</summary>

Projeto iniciado como MVP de monitoramento substituindo PaperCut em PME. Roadmap original tinha 5 fases; Fases 1–4 entregaram a Audit Platform. Requisitos v1.0 arquivados em `.planning/milestones/v1.0-REQUIREMENTS.md`.

</details>

---
*Last updated: 2026-05-27 after v1.0 milestone*
