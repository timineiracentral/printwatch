# MILESTONES — PrintWatch

Histórico de milestones entregues.

---

## v1.0 — Audit Platform

**Shipped:** 2026-05-27  
**Phases:** 4 (1–4) | **Plans:** 23 | **Timeline:** 2026-05-26 → 2026-05-27 (~2 dias de execução intensiva)

**Delivered:** Pipeline ponta-a-ponta CUPS → SQLite → FastAPI → Dashboard React com filtros, stats e export CSV; validado em VM real com jobs Windows.

**Key accomplishments:**
1. CUPS + Docker Compose operacional na rede com `page_log` estruturado e deploy VM documentado
2. Watcher Python com checkpoint inode/offset e persistência idempotente no SQLite
3. API REST `/api/v1` com jobs agregados, stats, export CSV pt-BR e índices de performance
4. Dashboard web nginx :80 com UI Apple/PaperCut, filtros URL, tabela paginada e export com filtros
5. Gaps de qualidade de dados (printer quote, username AD) investigados e fechados na Fase 3
6. Checkpoint humano aprovado na VM (`VM_HOST`) — critérios ROADMAP Fase 4 atendidos

**Known gaps at close (accepted):**
- SERVER-04, DEPLOY-03, DEPLOY-04 — fora do escopo v1.0; realocados para v1.5 / v3.0
- Sem auditoria formal `/gsd-audit-milestone` pré-close (recomendado retrospectivamente)
- Fase 3 sem SUMMARY.md por plan (verificação e código cobrem)

**Archives:**
- [v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)
- [v1.0-REQUIREMENTS.md](milestones/v1.0-REQUIREMENTS.md)

**Git tag:** `v1.0`

---

## v1.5 — Management Platform (active)

**Started:** 2026-05-27  
**Status:** 📋 Planejamento — Fase 5 requirements definidos  
**Phases:** 5–8 (continuação numérica)  
**Próximo passo:** Discussão arquitetural Fase 5 → `/gsd-plan-phase 5`

**Escopo:** Master data (impressoras, dept, usuários, CC), costing/chargeback interno, analytics gerencial, fleet online/offline, toner SNMP opt-in.

**Artefatos:** `.planning/REQUIREMENTS.md`, `.planning/ROADMAP.md`, `.planning/research/`
