# Phase 6: Costing & Chargeback — Context

**Gathered:** 2026-05-27  
**Status:** Ready for planning

<domain>
## Phase Boundary

Tarifas globais mono/color com **histórico de vigência**; custo estimado por job na API e coluna opcional na UI de auditoria; correção manual de `color_mode` em linhas sem classificação; exports CSV de chargeback (por centro de custo e por departamento); melhorias na captura CUPS para registrar mono/color de forma confiável.

**Cadeia alvo:** `cost_rates` (histórico) → calculadora no read path → `JobOut` + exports → Settings “Tarifas” + correção manual na auditoria.

**Invariants (herdados):**
- Watcher/captura append-only inalterados no hot path (cálculo e correção manual são pós-captura).
- Chargeback = alocação interna; sem fatura nem integração contábil.
- `outside_policy` permanece só em auditoria — **excluído** de chargeback e exports desta fase.

**Não inclui:** dashboard `/manager`, cards gerenciais, extensão visual de `/stats/summary` (Fase 7); tarifa por impressora (v1.6+); `outside_policy` nos relatórios de custo.

</domain>

<decisions>
## Implementation Decisions

### A. Modelo de tarifa e vigência

- **D-01:** Tabela `cost_rates` (ou equivalente) com histórico — cada registro: `rate_mono`, `rate_color`, `valid_from` (datetime/date), `is_active` ou encadeamento por vigência; **nunca** sobrescrever silenciosamente tarifa anterior.
- **D-02:** Custo de um job/linha usa a tarifa **vigente na data/hora do evento** (`print_jobs.timestamp`), não a tarifa “atual” do sistema.
- **D-03:** Admin gerencia tarifas em **nova seção Settings** (“Tarifas” / “Custos”) — criar nova vigência, visualizar histórico; moeda **BRL** com exibição `R$` e precisão adequada a centavos (2 casas na UI; cálculo interno pode usar Decimal).
- **D-04:** Tarifas **somente globais** nesta fase (sem override por impressora) — alinhado a REQUIREMENTS e FEATURES defer.

### B. Classificação mono vs color e páginas faturáveis

- **D-05:** Meta operacional: **sempre** registrar no log se a impressão foi colorida ou P&B — trabalho inclui CUPS/`page_log`/parser (ex. scripts e PPD como `scripts/fix-cups-color-queue.sh`) para maximizar preenchimento de `color_mode` na captura.
- **D-06:** Regra de billing: apenas linhas (`print_jobs`) com `color_mode` **classificado** entram no cálculo de páginas mono/color e custo; linhas com `color_mode` NULL = **páginas pendentes** — **não** contam em mono nem color até resolvidas.
- **D-07:** Classificação canônica no backend: mapear valores CUPS conhecidos → `mono` | `color`; valores desconhecidos tratados como pendentes (NULL ou flag explícita) até correção manual — planner define lista de aliases.
- **D-08:** **Correção manual** pelo admin na UI de auditoria (e API): permitir definir `mono` ou `color` por **linha bruta** `print_jobs` (1 linha = 1 folha no modelo atual); após salvar, a linha passa a ser **faturável** e entra em agregações/custo retroativamente no read path.
- **D-09:** Job agregado na API expõe, além de `pages` total do grupo: `pages_billable`, `pages_pending_color` (contagem de linhas NULL no grupo), `estimated_cost` (soma das linhas faturáveis × tarifa vigente), e breakdown opcional `pages_mono` / `pages_color` no grupo.
- **D-10:** Lista de jobs (`/`): coluna **custo estimado** opcional (toggle ou preferência local) — **sem** cards gerenciais nem alteração de `/stats/summary` nesta fase.

### C. Atribuição para chargeback

- **D-11:** Centro de custo do job (usuário cadastrado): **override** `users.cost_center_id` → senão `departments.cost_center_id` do dept do usuário → senão bucket **`Não atribuído`** (CC).
- **D-12:** **Usuário desconhecido** (username sem match em `users` ativo): bucket próprio **`Usuário não cadastrado`** — separado de “Não atribuído” (CC).
- **D-13:** `printer_id` NULL: bucket/linha **`Impressora não cadastrada`** — **não** misturar com alocação por CC/dept; jobs ainda podem mostrar custo por páginas faturáveis, mas export agrupa essa dimensão à parte.
- **D-14:** Jobs com `outside_policy = true` **excluídos** de todos os totais e exports de chargeback desta fase (permanecem visíveis na auditoria com badge existente).

### D. Exports chargeback (CHRG)

- **D-15:** **Dois** endpoints/arquivos CSV no mesmo intervalo de datas: `chargeback-by-cost-center.csv` e `chargeback-by-department.csv` (nomes finais a critério do planner).
- **D-16:** Colunas mínimas por agrupamento: identificador/nome do grupo, `pages_mono`, `pages_color`, `estimated_cost`, linha/bucket **`Não atribuído`**, e seção/bucket opcional **`Páginas pendentes`** (sem `color_mode` classificado no período).
- **D-17:** Buckets fixos adicionais no export (não misturados): `Usuário não cadastrado`, `Impressora não cadastrada`; **sem** coluna ou filtro `outside_policy`.
- **D-18:** Mesmos filtros de período que jobs/export existente (`date_from`, `date_to`, timezone SP herdado).

### E. API e limites Fase 6 vs 7

- **D-19:** Fase 6 entrega: CRUD/histórico tarifas, campos de custo em `/api/v1/jobs`, endpoints de export chargeback, API de correção manual `color_mode`, melhorias captura.
- **D-20:** **Não** estender `/api/v1/stats/summary` com custo nesta fase — Fase 7 (`/manager`) assume analytics visuais e agregações gerenciais.
- **D-21:** Endpoint de agregação de custo por dept/CC/usuário para relatórios pode existir se necessário aos exports (COST-04), mas **sem** UI de dashboard gerencial.

### F. Invariants

- **D-22:** Alterar tarifa ou corrigir `color_mode` **não** reescreve histórico de `print_jobs` além do campo de classificação; custo sempre derivado no read path.
- **D-23:** Falha em costing/settings **não** afeta watcher nem impressão física.

### Claude's Discretion

- UX exata da correção manual (modal vs inline vs drill-down no job agregado) desde que opere na linha `print_jobs`.
- Schema exato de `cost_rates` (`valid_to` calculado vs só `valid_from`).
- Lista de aliases `color_mode` CUPS → mono/color.
- Nomes de arquivo CSV e rotas REST finais.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap & requirements
- `.planning/ROADMAP.md` — Phase 6 goal and success criteria
- `.planning/REQUIREMENTS.md` — COST-01–04, CHRG-01–04, ORG-06 (unassigned CC)
- `.planning/PROJECT.md` — v1.5 principles, chargeback ≠ billing

### Prior phase context
- `.planning/phases/05-master-data-organization/05-CONTEXT.md` — org model, soft link username, CC ≠ dept
- `.planning/phases/05-2-user-printer-access-policy/05.2-CONTEXT.md` — `outside_policy` rules (exclude from chargeback)

### Research
- `.planning/research/SUMMARY.md` — cost on read, global rates first
- `.planning/research/ARCHITECTURE.md` — `cost_rates` + calculator, build order
- `.planning/research/FEATURES.md` — per-printer rates deferred v1.6+

### Code (integration)
- `backend/app/db/models.py` — `PrintJob`, `User`, `Department`, `CostCenter`
- `backend/app/services/jobs_service.py` — aggregated job query (extend for billable pages/cost)
- `backend/app/services/stats_service.py` — **do not** add cost here in phase 6
- `backend/app/services/csv_export.py` — pattern for streaming CSV exports
- `backend/app/schemas/jobs.py` — `JobOut` extension fields
- `frontend/src/pages/JobsPage.tsx`, `frontend/src/components/jobs/JobsTable.tsx` — optional cost column + manual correction entry point
- `scripts/fix-cups-color-queue.sh` — reference for CUPS color capture hardening

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `jobs_service._build_aggregated_query` — base for billable-page subqueries and cost rollup
- `csv_export.iter_csv_rows` / `export.py` — pattern for date-filtered streaming exports
- Settings routes under `/settings/*` — add `Tarifas` nav item alongside existing CRUD pages
- `policy_service.compute_outside_policy` — reuse to **exclude** rows from chargeback queries

### Established Patterns
- Jobs aggregated by `(printer, job_id, username, job_name, minute_bucket)`; cost must decompose to raw rows for pending-color logic
- Read-path enrichment (join users/dept/CC) already used for `outside_policy`
- Alembic migrations; SQLite WAL; no watcher SQLAlchemy org imports

### Integration Points
- New tables: `cost_rates` (+ optional `color_mode` audit column on `print_jobs` if manual correction needs `color_mode_source` enum: `captured` | `manual`)
- API: extend `GET /jobs`, `PATCH` correction endpoint, `GET /export/chargeback/...`, Settings CRUD rates
- Frontend: Settings “Tarifas” + Jobs table cost column + correction UI

</code_context>

<specifics>
## Specific Ideas

- Operador já investe em filas CUPS coloridas (`fix-cups-color-queue.sh`) — fase 6 deve documentar/validar `page_log` com `%C` confiável, não só calcular em cima de dados ruins.
- Chargeback CSVs são pares (CC + dept) com **mesmas datas** para conferência lado a lado.
- Páginas pendentes visíveis no export incentivam TI a corrigir ou ajustar CUPS antes de fechar mês.

</specifics>

<deferred>
## Deferred Ideas

- Tarifa por impressora — v1.6+ (`.planning/research/FEATURES.md`)
- `outside_policy` em relatórios de custo — explicitamente fora desta fase
- Dashboard `/manager`, comparativos, tops com custo — Fase 7
- Email agendado de chargeback — v1.6+

</deferred>

---

*Phase: 06-costing-chargeback*  
*Context gathered: 2026-05-27*
