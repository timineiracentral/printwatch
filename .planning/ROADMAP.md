# ROADMAP — PrintWatch

**Projeto:** PrintWatch — gestão e auditoria de impressão self-hosted  
**Milestone ativa:** v1.5 Management Platform  
**Última atualização:** 2026-05-27

---

## Milestones

| Versão | Nome | Fases | Status | Arquivo |
|--------|------|-------|--------|---------|
| **v1.0** | Audit Platform | 1–4 | ✅ Shipped 2026-05-27 | [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md) |
| **v1.5** | Management Platform | 5–8 | 📋 Planejamento | este arquivo |
| **v2.0** | Operations & Insights | TBD | 📋 Futuro | — |
| **v3.0** | Production & Control | TBD | 📋 Futuro | — |

---

## ✅ v1.0 Audit Platform (SHIPPED)

<details>
<summary>Fases 1–4</summary>

| # | Fase | Plans | Concluída |
|---|------|-------|-----------|
| 1 | Infrastructure & Print Server | 5/5 | 2026-05-26 |
| 2 | Log Pipeline & Data Layer | 5/5 | 2026-05-26 |
| 3 | Backend API | 6/6 | 2026-05-27 |
| 4 | Dashboard Web | 7/7 | 2026-05-27 |

Requisitos: [milestones/v1.0-REQUIREMENTS.md](milestones/v1.0-REQUIREMENTS.md)

</details>

---

## 📋 v1.5 Management Platform

**Promessa:** Cadastro operacional (impressoras, departamentos, usuários, centros de custo), custos e chargeback interno, analytics gerencial e saúde da frota — mantendo captura append-only e impressão sempre disponível.

**Princípios:** Monólito · SQLite · Docker Compose · PaperCut-like ops · sem overengineering

**Research:** `.planning/research/SUMMARY.md`  
**Requirements:** `.planning/REQUIREMENTS.md` (47 REQ)

---

### Phase 5: Master Data & Organization

**Goal:** Admin cadastra impressoras, departamentos, centros de custo e usuários; importa CSV; jobs históricos e novos vinculam a `printer_id` sem alterar o hot path do watcher.

**Requirements:** ORG-01–09, INV-01–06, IMPORT-01–05, SETTINGS-01–04, DATA-04–07, SERVER-04  
**Plans:** 7/7 plans complete

| Wave | Plans | Entrega |
|------|-------|---------|
| 1 | 05-01 | Alembic + schema mestre + CORS + WAL |
| 2 | 05-02, 05-03, 05-04 | normalize core + CRUD printers + CRUD org |
| 3 | 05-05, 05-06 | matcher/backfill + import CSV |
| 4 | 05-07 | Settings UI + react-router + FilterBar registry |

**Success criteria:**
1. Admin CRUD completo para printers, departments, cost-centers, users via Settings UI
2. CSV import com validação por linha e templates downloadáveis
3. `printer_id` preenchido em jobs novos (matcher) e backfill executável para histórico
4. Watcher e impressão física inalterados quando backend/settings indisponíveis
5. Audit dashboard (jobs) permanece funcional com nova navegação Settings
6. CC e Department gerenciados como entidades independentes

**Context:** `.planning/phases/05-master-data-organization/05-CONTEXT.md` (gate ✅)  
**Discussion log:** `05-DISCUSSION-LOG.md`

---

### Phase 6: Costing & Chargeback

**Goal:** Tarifas mono/color configuráveis; custo estimado por job; relatórios e export CSV de chargeback interno por departamento e centro de custo.

**Requirements:** COST-01–04, CHRG-01–04

**Success criteria:**
1. Admin define tarifa global mono e color
2. Lista de jobs exibe custo estimado quando rates configurados
3. Export chargeback CSV por CC e por departamento com split mono/color
4. Bucket "não atribuído" visível para jobs/usuários sem cadastro
5. Nenhuma geração de fatura ou integração contábil

---

### Phase 7: Manager Analytics

**Goal:** Dashboard gerencial com consumo, custo, rankings e comparação período a período.

**Requirements:** ANAL-01–05

**Success criteria:**
1. Rota `/manager` com cards de período (páginas + custo)
2. Top 10 usuários, impressoras e departamentos
3. Comparativo vs período anterior
4. Carregamento < 3s para janela de 90 dias (dataset típico)
5. Separado do audit jobs table

---

### Phase 8: Fleet Health & Toner

**Goal:** Status online/offline por impressora (CUPS/IPP → ping); toner SNMP opt-in como telemetria.

**Requirements:** FLEET-01–05, TONER-01–04

**Success criteria:**
1. Fleet overview com status e última verificação
2. Checker em background — falha não afeta captura/API core
3. Status primário via CUPS/IPP; fallback ping IP
4. Toner % por impressora com SNMP habilitado
5. Sem módulo de estoque de consumíveis

---

## Progress

| Fase | Milestone | REQ | Plans | Status |
|------|-----------|-----|-------|--------|
| 1–4 | v1.0 | 22 | 23/23 | ✅ Complete |
| 5 | v1.5 | 7/7 | Complete   | 2026-05-27 |
| 6 | v1.5 | 8 | — | Scoped |
| 7 | v1.5 | 5 | — | Scoped |
| 8 | v1.5 | 9 | — | Scoped |

---

## Fora de escopo (v1.5)

- Microserviços, PostgreSQL, LDAP, auth, cotas com bloqueio
- Faturamento contábil, estoque de toner
- DEPLOY-03/04 → v3.0
- Paridade PaperCut enterprise

---

## Próximos passos

1. `/gsd-plan-phase 5` — gerar plans (arquitetura aprovada 2026-05-27)

---
*Roadmap v1.5 — 2026-05-27*
