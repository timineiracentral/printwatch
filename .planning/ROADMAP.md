# ROADMAP — PrintWatch

**Projeto:** PrintWatch — gestão e auditoria de impressão self-hosted  
**Milestone ativa:** v1.5 Management Platform (planejamento)

---

## Milestones

| Versão | Nome | Fases | Status | Arquivo |
|--------|------|-------|--------|---------|
| **v1.0** | Audit Platform | 1–4 | ✅ Shipped 2026-05-27 | [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md) |
| **v1.5** | Management Platform | 5+ | 📋 Planejamento | — |
| **v2.0** | Operations & Insights | TBD | 📋 Futuro | — |
| **v3.0** | Production & Control | TBD | 📋 Futuro | — |

---

## ✅ v1.0 Audit Platform (SHIPPED 2026-05-27)

<details>
<summary>Fases 1–4 — auditoria de impressão ponta-a-ponta</summary>

| # | Fase | Plans | Concluída |
|---|------|-------|-----------|
| 1 | Infrastructure & Print Server | 5/5 | 2026-05-26 |
| 2 | Log Pipeline & Data Layer | 5/5 | 2026-05-26 |
| 3 | Backend API | 6/6 | 2026-05-27 |
| 4 | Dashboard Web | 7/7 | 2026-05-27 |

**Entregue:** CUPS → watcher → SQLite → API `/api/v1` → dashboard React (filtros, stats, CSV).

Requisitos arquivados: [milestones/v1.0-REQUIREMENTS.md](milestones/v1.0-REQUIREMENTS.md)

</details>

---

## 📋 v1.5 Management Platform (próxima)

**Promessa:** Cadastro de impressoras e organização (departamentos/usuários), custos por página mono/color, analytics por departamento e base para inventário operacional.

**Não inclui nesta milestone:** LDAP, cotas/bloqueio ativo, deploy/hardening final (v3.0).

### Direção das fases (rascunho — detalhar via `/gsd-new-milestone`)

| # | Fase (provisória) | Foco |
|---|-------------------|------|
| 5 | Master Data & Organization | CRUD impressoras, departamentos, usuários; backfill `printer_id` |
| 6 | Costing & Chargeback | Tarifas mono/color; stats/export por dept/usuário |
| 7 | Manager Analytics | Dashboard gerencial; insights de consumo |
| 8 | Fleet Health & Toner | Status online/offline; SNMP toner (opt-in) |

**Requisitos herdados da antiga Fase 5:** SERVER-04 → Fase 5; DEPLOY-03/04 → milestone v3.0.

**Próximo passo:** `/gsd-new-milestone` → requirements v1.5 → redesign completo do roadmap.

---

## Progress

| Fase | Milestone | Plans | Status | Completed |
|------|-----------|-------|--------|-----------|
| 1. Infrastructure & Print Server | v1.0 | 5/5 | Complete | 2026-05-26 |
| 2. Log Pipeline & Data Layer | v1.0 | 5/5 | Complete | 2026-05-26 |
| 3. Backend API | v1.0 | 6/6 | Complete | 2026-05-27 |
| 4. Dashboard Web | v1.0 | 7/7 | Complete | 2026-05-27 |
| 5+. Management Platform | v1.5 | — | Not started | — |

---

## Fora de escopo (v1.5 inicial)

- Microserviços / message bus
- PostgreSQL (reavaliar só com evidência de escala)
- Paridade completa PaperCut (chargeback contábil, follow-me, driver store)
- Multi-site / agentes remotos

---

*Última atualização: 2026-05-27 — milestone v1.0 encerrada*
