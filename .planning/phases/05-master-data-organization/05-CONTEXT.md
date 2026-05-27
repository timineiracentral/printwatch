# Phase 5: Master Data & Organization — Context

**Gathered:** 2026-05-27  
**Status:** ✅ Ready for planning (architecture gate closed)

<domain>
## Phase Boundary

Cadastro operacional de impressoras, departamentos, centros de custo e usuários; import CSV; Settings UI; vínculo de `print_jobs` a impressoras via `printer_id` **sem alterar o hot path do watcher**.

**Cadeia alvo:** `Registry (SQLite) + Matcher (background) → API CRUD/import → Settings UI` + audit dashboard inalterado em captura.

**Não inclui:** custos/chargeback (Fase 6), dashboard gerencial (Fase 7), fleet/SNMP (Fase 8), LDAP, auth na app, hard delete na UI, FK `user_id` em jobs.

</domain>

<decisions>
## Implementation Decisions

### A. Printer matching & `printer_id`

- **D-01:** Watcher **não** resolve `printer_id` no INSERT; coluna nullable.
- **D-02:** Matcher periódico **60s** — atualiza **somente** `print_jobs WHERE printer_id IS NULL`, em **batches limitados** (evitar full scan).
- **D-03:** **On-save printer** — match imediato para jobs órfãos daquela `cups_queue_name` normalizada.
- **D-04:** `POST /api/v1/admin/backfill-printer-ids` — reprocessamento histórico completo, **idempotente**, acionável manualmente.
- **D-05:** Matching usa `normalize_printer_name()` compartilhado — mesma regra em watcher ingest label, API, matcher e import.

### B. User ↔ Job linking

- **D-06:** **Soft link** — `print_jobs.username` raw preservado; join read-time com `users.cups_username` (exact match).
- **D-07:** **Sem FK** `user_id` em `print_jobs` nesta fase (aliases AD, inconsistências reais).

### C. Settings UI & navigation

- **D-08:** Rotas `/settings/*` (printers, departments, cost-centers, users, import) no **AppShell** existente.
- **D-09:** UX **operacional** (`/` audit jobs) separada de **gerencial** (`/manager` = Fase 7).
- **D-10:** Menu lateral simples, PaperCut-like; formulários e tabelas enxutos — workflows rápidos de TI, não CRUD enterprise.

### D. Printer registry & discovery

- **D-11:** Tabela `printers` + API registry = **fonte canônica** (substitui DISTINCT como primário).
- **D-12:** `GET /api/v1/printers/unmapped-queues` — filas no log sem cadastro (onboarding).
- **D-13:** UI Settings destaca impressoras **descobertas mas não cadastradas** (call-to-action para cadastro).
- **D-14:** `cups_queue_name` **globalmente único** — identidade operacional da fila CUPS; `display_name` pode repetir.

### E. Organization entities

- **D-15:** `departments` e `cost_centers` são entidades **distintas**; dept pode referenciar CC opcionalmente.
- **D-16:** `code` obrigatório em dept e CC; validação **case-insensitive**; persistência **UPPERCASE**; unicidade por código.
- **D-17:** `users.cups_username` unique; match exato ao username do log.
- **D-18:** Apenas **soft-delete** (`is_active=false`) na UI; hard delete só intervenção manual no banco.

### F. Schema & migrations

- **D-19:** **Alembic** obrigatório (`backend/alembic/`); sem migrations SQL manuais ad-hoc.
- **D-20:** Novas tabelas: `printers`, `departments`, `cost_centers`, `users`; `print_jobs.printer_id` nullable FK + índice.
- **D-21:** Índice composto ou parcial útil para matcher: `printer_id IS NULL` (+ `printer` se necessário para performance).
- **D-22:** SQLite WAL; transações curtas em backfill/matcher.

### G. CSV import

- **D-23:** **Partial commit** por padrão; `?strict=true` para all-or-nothing.
- **D-24:** Resposta de import inclui relatório: total, criados, atualizados, ignorados, erros por linha (número + mensagem).
- **D-25:** Templates CSV downloadáveis por entidade.
- **D-26:** Normalização de códigos dept/CC para UPPERCASE no import.

### H. Security & auth (v1.5)

- **D-27:** **Sem auth** na aplicação nesta fase — rede local.
- **D-28:** API e frontend **não** assumem sessão/login; nginx basic auth futuro via camada reversa **sem refactor** (sem middleware auth obrigatório no FastAPI agora).

### I. Invariants (non-negotiable)

- **D-29:** Falha em import, matcher, registry ou qualquer endpoint de settings **não** afeta watcher nem impressão física.
- **D-30:** Watcher não importa modelos SQLAlchemy de org — no máximo `app.core.normalize`.
- **D-31:** Capture pipeline e master data **desacoplados** — sem triggers de FK no INSERT de jobs.

</decisions>

<domain_model>
## Entity Model (approved)

```
CostCenter (1) ──< Department (N)     [department.cost_center_id optional]
Department (1) ──< User (N)
CostCenter (1) ──< User (N)           [user.cost_center_id optional override]
Department (1) ──< Printer (N)        [optional location]
Printer (1) ──< PrintJob (N)          [printer_id nullable FK]
PrintJob.username ──soft──> User.cups_username
```

### Schema notes

- `cost_centers.code`, `departments.code` — NOT NULL, UNIQUE, stored UPPERCASE
- `printers.cups_queue_name` — NOT NULL, UNIQUE (normalized comparison at match time)
- `users.cups_username` — NOT NULL, UNIQUE (raw CUPS string)
- All master tables: `is_active`, `created_at`, `updated_at`

</domain_model>

<api_surface>
## Minimum API Surface

| Method | Path | Decision |
|--------|------|----------|
| CRUD | `/api/v1/printers` | D-11, D-14 |
| CRUD | `/api/v1/departments` | D-15–16 |
| CRUD | `/api/v1/cost-centers` | D-15–16 |
| CRUD | `/api/v1/users` | D-17 |
| GET | `/api/v1/printers/unmapped-queues` | D-12 |
| POST | `/api/v1/import/{entity}` | D-23–24 |
| GET | `/api/v1/import/templates/{entity}` | D-25 |
| POST | `/api/v1/admin/backfill-printer-ids` | D-04 |

Audit endpoints (`/jobs`, `/export/csv`, `/stats/summary`) — **sem breaking changes** na Fase 5.

</api_surface>

<suggested_plan_order>
## Suggested Plan Breakdown (for plan-phase)

1. Alembic setup + migrations (entities + `printer_id` column)
2. Shared `normalize.py` + refactor Fase 3 usage
3. CRUD APIs (printers → cost_centers → departments → users)
4. Matcher service + lifespan task + admin backfill endpoint
5. Import CSV + templates + report schema
6. Settings UI (printers + unmapped highlight → org entities → import)
7. Integration: FilterBar printer source migration + validation scripts

</suggested_plan_order>

<references>
## References

- `.planning/REQUIREMENTS.md` — Phase 5 detailed (28 REQ)
- `.planning/phases/05-master-data-organization/05-DISCUSSION-LOG.md` — audit trail
- `.planning/research/PITFALLS.md` — capture coupling warnings
- `backend/app/db/models.py` — current schema
- `.planning/phases/03-backend-api/03-02-PLAN.md` — normalize_printer_name origin

</references>

---
*Architecture approved: 2026-05-27 — Proceed to `/gsd-plan-phase 5`*
