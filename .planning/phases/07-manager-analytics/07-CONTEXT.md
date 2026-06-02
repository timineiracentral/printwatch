# Phase 7: Manager Analytics — Context

**Gathered:** 2026-06-02  
**Status:** Ready for planning

<domain>
## Phase Boundary

Dashboard gerencial em **`/manager`**, separado da auditoria em `/`, com:

1. **Analytics por jobs (ANAL-01–05):** cards de período (páginas + custo estimado), comparativo vs período anterior, top 10 usuários / impressoras / departamentos, carregamento alvo **< 3s** para janela de 90 dias em dataset típico (20–100 usuários).
2. **MVP contadores de impressora (expansão acordada):** leituras periódicas manuais + import CSV; histórico temporal; estimativa de custo por **delta de contador × tarifa vigente**; seção dedicada abaixo dos rankings; **sem** coleta SNMP/IPP automática nesta fase (Fase 8).

**Cadeia jobs:** `print_jobs` + org (Fases 5–5.2) + `cost_service` / `cost_rates` (Fase 6) → novo endpoint manager → UI React.

**Cadeia contadores:** `printer_meter_readings` (novo) + registry `printer_id` → delta no intervalo → custo estimado por dispositivo → reconciliação informativa vs jobs.

**Invariants (herdados):**
- Chargeback e alocação por dept/CC permanecem **fonte jobs** (Fase 6); contador é visão operacional/financeira **agregada por dispositivo**, não substitui auditoria por usuário.
- `outside_policy` **excluído** de totais/rankings/custo por jobs (alinhado chargeback).
- Watcher/captura inalterados no hot path; falhas em analytics não bloqueiam impressão.

**Pré-requisito operacional (go-live):** `color_mode` mono|color confiável para custo por job — captura (`page_log` + parser + aliases CUPS + `scripts/fix-cups-color-queue.sh`) + correção manual (PATCH). Manager exibe volume **pendente de classificação**; bloqueador operacional se >X% do período piloto sem `color_mode` sem plano de correção (UI + UAT/runbook).

**Não inclui nesta fase:** coleta automática SNMP/IPP de contadores (→ Fase 8 com fleet/toner); gráficos de série temporal avançados; export CSV do manager (permanece Jobs/chargeback); substituir chargeback por contador; faturamento contábil.

</domain>

<decisions>
## Implementation Decisions

### A. Período, URL e comparativo (ANAL-01, ANAL-03)

- **D-01:** Presets iguais à auditoria (Fase 4): **Hoje**, **Últimos 7 dias**, **Mês atual** + intervalo **custom** (`date_from` / `date_to`) via date picker; **fonte da verdade = URL** (`searchParams`), timezone `America/Sao_Paulo`.
- **D-02:** Período **padrão** ao abrir `/manager`: **últimos 30 dias** (rolling, não mês calendário).
- **D-03:** Período anterior para comparativo — **modo híbrido** (discrição planner): preset **Mês atual** → mês calendário anterior completo; presets **Hoje / 7 / 30 / 90 / custom** → mesma duração imediatamente antes do intervalo selecionado.
- **D-04:** Exibição do comparativo nos cards KPI — **valor atual + delta % vs anterior** (verde/vermelho discreto, estilo Fase 4) + valor anterior em texto secundário menor.

### B. Regras de custo e páginas (jobs / ANAL)

- **D-05:** Totais de **páginas e custo** nos cards usam apenas linhas **faturáveis** (`color_mode` classificado); volume **pendente** (sem `color_mode`) em card/linha separada, não somado aos totais faturáveis.
- **D-06:** Jobs com `outside_policy = true` **excluídos** de totais, comparativo e rankings (mesma regra chargeback Fase 6).
- **D-07:** Sem tarifa configurada/vigente no período: campos de custo mostram **"—"** ou **"Sem tarifa"**; páginas continuam visíveis; aviso discreto opcional.
- **D-08:** Buckets sintéticos (`Usuário não cadastrado`, `Impressora não cadastrada`, `Não atribuído`) **entram nos totais**; nos **top 10** aparecem como linhas normais quando no ranking (não excluir artificialmente).

### C. Rankings Top 10 (ANAL-02)

- **D-09:** Layout: **três tabelas compactas empilhadas** (usuários → impressoras → departamentos), estilo lista PaperCut / Apple HIG (Fase 4).
- **D-10:** Ordenação default: **por páginas (volume)**; coluna **custo estimado** quando tarifas existirem (secundária).
- **D-11:** Ranking **departamentos:** atribuição via **departamento do usuário cadastrado** (`username` → `users.department_id`); jobs sem usuário cadastrado → bucket sintético no ranking.
- **D-12:** **Sem gráficos/charts** nesta fase — cards numéricos + tabelas + comparativo % apenas (requisitos ANAL cobertos sem lib de charts).

### D. Breakdown mono/color e pendências

- **D-13:** Cards de resumo: um card **Páginas** com subtítulo **"X mono · Y color"** + card(s) de **custo** (total); não duplicar em quatro cards separados no MVP.
- **D-14:** Pendências: card/linha de alerta **somente se count > 0** no período, com link para auditoria (`/` com filtro de pendentes / fluxo correção manual Fase 6).
- **D-15:** Tabelas top 10: colunas **Páginas total | Custo**; breakdown mono/color nos cards, não obrigatório em cada linha do top.
- **D-16:** Go-live `color_mode`: **banner** no `/manager` se % pendente > limiar (planner define, sugestão 5%) **+** checklist UAT/runbook; não bloquear renderização da página.

### E. API, performance e navegação (ANAL-04, ANAL-05)

- **D-17:** Novo namespace **`GET /api/v1/manager/summary`** (ou nome equivalente) com `date_from`, `date_to` — **payload único**: KPIs + comparativo + tops + pendências + flags tarifa; **não** estender `/stats/summary` (mantém contrato Fase 3/4 para home).
- **D-18:** Implementação backend deve reutilizar `_build_aggregated_subquery` / padrões `cost_service` onde aplicável; índices e agregações SQL para meta **< 3s** em 90 dias.
- **D-19:** **Manter** `SummaryCards` na home `/` como atalho operacional TI; `/manager` é visão gerencial completa; link opcional "Ver analytics" na home (discrição UI).
- **D-20:** Sidebar: item principal **entre Jobs e Settings** — label sugerida **"Gerencial"** ou **"Analytics"** (ícone discreto).
- **D-21:** **Sem** export CSV novo no `/manager` nesta fase — exports permanecem Jobs + chargeback (Fase 6).

### F. MVP contadores de impressora (METER — expansão Fase 7)

- **D-22:** Nova entidade leituras, ex.: `printer_meter_readings`: `(timestamp, printer_id, counter_total, counter_mono?, counter_color?, source=manual|import)`; histórico append-only; última leitura por impressora consultável.
- **D-23:** Entrada **manual** na UI (ficha impressora em Settings e/ou ação na seção manager) + **import CSV** (`printer` code ou id, timestamp, total, mono opcional, color opcional).
- **D-24:** **Sem** poll SNMP/IPP automático de contadores na Fase 7 — automação compartilhada com Fase 8 (fleet/toner); documentar spike SNMP HP/Samsung antes de prometer auto.
- **D-25:** Custo por delta: se hardware expõe **mono + color**, aplicar tarifas respectivas no delta; se **só total**, usar **proporção mono/color dos jobs** da mesma impressora no período (fallback) — exibir nota quando proporcional.
- **D-26:** Seção UI **abaixo dos três tops**: tabela por impressora — leitura inicial/final no período, **páginas pelo contador** (delta), **custo estimado por contador**, **páginas pelos jobs**, coluna **divergência** (informativa; alerta visual se |Δ| > limiar — planner define, sugestão 5% ou N páginas).
- **D-27:** Mesmo filtro de datas da URL do `/manager` aplica-se à seção contadores.
- **D-28:** Contador **não** alimenta chargeback por dept/CC; jobs permanecem fonte para CHRG.

### G. Novos requisitos propostos (planner adiciona a REQUIREMENTS.md)

| ID | Resumo |
|----|--------|
| **METER-01** | Admin registra leitura manual de contador por impressora cadastrada |
| **METER-02** | Admin importa leituras via CSV |
| **METER-03** | Sistema calcula delta de páginas por impressora em intervalo de datas |
| **METER-04** | Sistema estima custo no período por delta × tarifa vigente (com regra D-25) |
| **METER-05** | Manager exibe tabela contador vs jobs com divergência informativa |
| **METER-06** | Histórico de leituras consultável por impressora (últimas N ou no período) |

### Claude's Discretion

- Rotas REST finais, nomes de query params e shape exato do JSON `ManagerSummaryResponse`.
- Limiar % pendente `color_mode` e divergência contador/jobs.
- UX exata do link pendências → auditoria / modal correção.
- Ordenação alternável páginas↔custo nos tops (se baixo esforço; default D-10).
- Schema Alembic detalhado e validações CSV import.
- Spike SNMP documentado em RESEARCH.md, sem implementar auto nesta fase.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap & requirements
- `.planning/ROADMAP.md` — Phase 7 goal, success criteria (ANAL); **atualizar** com METER após plan
- `.planning/REQUIREMENTS.md` — ANAL-01–05; adicionar METER-01–06
- `.planning/PROJECT.md` — v1.5 principles, analytics ≠ capture hot path

### Prior phase context
- `.planning/phases/04-dashboard-web/04-CONTEXT.md` — Apple HIG, presets URL, cards, sem charts na auditoria
- `.planning/phases/05-master-data-organization/05-CONTEXT.md` — org, `printer_id`, registry
- `.planning/phases/05-2-user-printer-access-policy/05.2-CONTEXT.md` — `outside_policy`
- `.planning/phases/06-costing-chargeback/06-CONTEXT.md` — tarifas, faturável, chargeback, **não** estender `/stats/summary` com custo

### Research
- `.planning/research/SUMMARY.md` — Phase 7 rationale, build order
- `.planning/research/ARCHITECTURE.md` — `stats/manager` endpoints, parallel to `/stats/summary`
- `.planning/research/FEATURES.md` — manager analytics P1

### Code (integration)
- `backend/app/services/stats_service.py` — padrão buckets; **não** adicionar custo aqui
- `backend/app/services/cost_service.py` — `line_cost`, `aggregate_cost_by_dimension`, `rate_at`
- `backend/app/services/jobs_service.py` — `_build_aggregated_subquery`, enrich cost
- `backend/app/api/v1/stats.py` — manter contrato legado home
- `frontend/src/pages/JobsPage.tsx`, `frontend/src/components/summary/SummaryCards.tsx` — home atalho
- `frontend/src/components/filters/FilterBar.tsx` — reutilizar presets/URL pattern
- `frontend/src/routes/index.tsx` — adicionar `/manager`
- `frontend/src/components/layout/Sidebar.tsx` — nav item
- `scripts/fix-cups-color-queue.sh` — captura color_mode

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `FilterBar` + URL `searchParams` — mesmo modelo de período em `/manager`
- `SummaryCard` / grid cards — KPIs e comparativo %
- `cost_service.aggregate_cost_by_dimension` — lógica de custo por dimensão org (referência, não endpoint final)
- `stats_service._compute_bucket` — padrão tops por páginas (estender com custo + `date_from`/`date_to`)
- Settings `PrintersPage` — ponto de entrada leitura manual por impressora
- `import_service` — padrão CSV upsert para METER import

### Established Patterns
- Agregação via `_build_aggregated_subquery` (jobs); custo no read path
- TanStack Query + `staleTime` para summary
- AppShell + PageHeader + design tokens Fase 4
- Alembic migrations; SQLite WAL

### Integration Points
- Novo router `backend/app/api/v1/manager.py` + `include_router` em `__init__.py`
- Nova página `frontend/src/pages/ManagerPage.tsx` (ou equivalente)
- Nova migration `printer_meter_readings`
- Seção contadores como componente filho de ManagerPage

</code_context>

<specifics>
## Specific Ideas

- Expansão de escopo: usuário escolheu **opção C** — ANAL completo + MVP contadores manual/CSV na mesma fase (não backlog v1.6).
- Contadores: seção **abaixo** dos três rankings; reconciliação contador vs jobs **informativa**, não substitui chargeback.
- Pré-requisito explícito: custo por job depende de `color_mode`; operação deve rodar fix CUPS por fila antes de confiar nos números gerenciais.
- Roadmap original ANAL-01..05 **permanece**; METER é acréscimo — planner deve atualizar ROADMAP e REQUIREMENTS.

</specifics>

<deferred>
## Deferred Ideas

- Coleta **automática** SNMP/IPP de contadores — Fase 8 (compartilhar poll com fleet online/toner; endpoint ou job separado do manager request path).
- Gráficos de série temporal (trend/sparkline) — v1.6+ ou fase dedicada.
- Export CSV do resumo manager — permanece fora; usar chargeback/jobs exports.
- Toggle ordenação páginas↔custo nos tops — nice-to-have se sobrar capacidade.
- Ranking duplo dept **e** CC na mesma view — defer; Fase 7 usa dept do usuário (D-11).
- Aba separada "Por jobs | Por contador" — defer; seção única abaixo dos tops (escolha do usuário).

### Reviewed Todos (not folded)
- `GAP-02-01-parser-printer-quote` (match fraco por keywords) — não relacionado a analytics; manter fora do escopo Fase 7.

</deferred>

---

*Phase: 7-Manager Analytics*  
*Context gathered: 2026-06-02*
