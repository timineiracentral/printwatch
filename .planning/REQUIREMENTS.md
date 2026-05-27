# REQUIREMENTS — PrintWatch v1.5 Management Platform

**Defined:** 2026-05-27  
**Milestone:** v1.5  
**Core Value:** Gestão operacional de impressão — cadastro, custos, analytics e fleet — sem interromper captura ou impressão física.

**Research:** `.planning/research/SUMMARY.md`

---

## v1.5 Requirements

### Organization — Departments (ORG)

- [x] **ORG-01**: Admin can create, edit, and deactivate a department with name and optional code
- [x] **ORG-02**: Admin can list departments with search/filter by name or code
- [x] **ORG-03**: Deactivated department does not accept new user assignments but preserves historical references

### Organization — Cost Centers (ORG)

- [x] **ORG-04**: Admin can create, edit, and deactivate a cost center independent of departments
- [x] **ORG-05**: Admin can optionally link a department to a cost center (many departments may share one CC)
- [x] **ORG-06**: A department without CC assignment appears as "unassigned" in chargeback reports (Fase 6)

### Organization — Users (ORG)

- [x] **ORG-07**: Admin can register a user with CUPS username (exact match key), display name, department, and optional cost center override
- [x] **ORG-08**: Admin can list users with filter by department, cost center, or username
- [x] **ORG-09**: Print jobs from unknown usernames remain visible in audit views and appear as "unassigned" in management reports

### Inventory — Printers (INV)

- [x] **INV-01**: Admin can register a printer with display name, CUPS queue name, IP address, manufacturer/model, location, and optional department
- [x] **INV-02**: Admin can edit printer metadata and deactivate a printer (historical jobs preserved)
- [x] **INV-03**: Admin can list printers showing registration status: mapped jobs vs unmapped queue names from log
- [x] **INV-04**: System links historical print jobs to `printer_id` via normalized CUPS queue name match (batch/backfill)
- [x] **INV-05**: New print jobs receive `printer_id` when queue name matches a registered printer (async or post-insert, never blocking watcher)
- [x] **INV-06**: `/api/v1/printers` registry replaces DISTINCT-log behavior as canonical printer list (audit UI migrates to registry)

### Import (IMPORT)

- [x] **IMPORT-01**: Admin can upload CSV to bulk create/update departments
- [x] **IMPORT-02**: Admin can upload CSV to bulk create/update cost centers
- [x] **IMPORT-03**: Admin can upload CSV to bulk create/update users (username, name, department code, optional CC code)
- [x] **IMPORT-04**: Import returns per-row validation errors without failing entire file when configured for partial success
- [x] **IMPORT-05**: CSV templates are downloadable from Settings UI

### Settings UI (SETTINGS)

- [x] **SETTINGS-01**: Dashboard has a Settings section with navigation for Printers, Departments, Cost Centers, Users, and Import
- [x] **SETTINGS-02**: CRUD forms follow existing UI patterns (Fase 4 design system)
- [x] **SETTINGS-03**: Settings changes do not require restart of watcher or CUPS containers
- [x] **SETTINGS-04**: Audit dashboard (jobs/history) remains available unchanged alongside Settings

### Data & Schema (DATA)

- [x] **DATA-04**: Alembic migrations manage new tables: `printers`, `departments`, `cost_centers`, `users`
- [x] **DATA-05**: `print_jobs.printer_id` nullable FK added without breaking existing ingest
- [x] **DATA-06**: SQLite WAL mode enabled for concurrent reads during backfill (if not already)
- [x] **DATA-07**: Schema supports soft-delete (`is_active`) on master data entities

### Server (SERVER) — deferred from v1.0

- [x] **SERVER-04**: Admin can view printer registration and mapping status in UI (fulfills v1.0 deferral)

---

### User–Printer Access (ACCESS) — Fase 5.2

**Policy model (decisions locked):** N:N User ↔ Printer via `user_printer_access`; **permissive** — missing assignment or print on non-assigned printer does **not** block physical print; informs TI and reporting only. One CUPS queue per registered printer (1:1). Client choice = Windows IPP; PrintWatch audits queue used. TI installs printers on PC; product exports setup list.

- [ ] **ACCESS-01**: Admin can assign printers to a user via `user_printer_access` (`is_active`, `is_default`); at most one default per user; API CRUD on user and/or printer scope
- [ ] **ACCESS-02**: User detail in Settings shows allowed printers and lets admin set/clear default among active assignments
- [ ] **ACCESS-03**: Printer detail optionally shows users with access (inverted view); changes sync with user-side assignments
- [ ] **ACCESS-04**: Printer create/edit selects queue from detected unmapped (and future discovered) queues; primary UI labels avoid "CUPS" jargon
- [ ] **UX-05-02**: Printer create flow uses detected-queue picker (`unmapped-queues` minimum); label **Identificador no servidor** for manual `cups_queue_name` only in advanced/collapsed section
- [ ] **ACCESS-05**: Admin can export per-user TI setup guide (display_name, queue name, ipp_url, is_default); jobs list and/or CSV export show read-only **outside policy** when a **registered** user prints on a printer not in their allowed list

**Out of scope 5.2:** CUPS/job blocking (v2.5 POLICY), department inheritance, end-user self-service portal, dashboard auth/login.

---

### Costing (COST) — Fase 6

- [x] **COST-01**: Admin can configure global cost per page for monochrome and color
- [x] **COST-02**: System calculates estimated job cost from page count, color mode, and active rates
- [x] **COST-03**: API exposes cost fields on job list and detail when rates configured
- [x] **COST-04**: Stats endpoint supports aggregation of cost by department, user, and cost center

### Chargeback (CHRG) — Fase 6

- [x] **CHRG-01**: Admin can export chargeback CSV for a date range grouped by cost center
- [x] **CHRG-02**: Admin can export chargeback CSV grouped by department
- [x] **CHRG-03**: Chargeback export includes page counts (mono/color split), estimated cost, and unassigned bucket
- [x] **CHRG-04**: Chargeback is internal reporting only — no invoice generation or accounting integration

---

### Manager Analytics (ANAL) — Fase 7

- [ ] **ANAL-01**: Manager can view a dashboard with total pages and cost for selected period
- [ ] **ANAL-02**: Manager can see top users, printers, and departments by volume and cost
- [ ] **ANAL-03**: Manager can compare current period vs previous period (pages/cost)
- [ ] **ANAL-04**: Manager dashboard loads within 3s for 90-day window on typical dataset (20–100 users)
- [ ] **ANAL-05**: Manager dashboard is separate route from audit jobs table (e.g. `/manager`)

---

### Fleet (FLEET) — Fase 8

- [ ] **FLEET-01**: System checks printer online status via CUPS/IPP as primary method
- [ ] **FLEET-02**: System falls back to IP ping when CUPS/IPP status unavailable
- [ ] **FLEET-03**: Fleet status stored with last-checked timestamp; API serves cached status
- [ ] **FLEET-04**: Admin can view fleet overview list with online/offline/unknown per printer
- [ ] **FLEET-05**: Fleet checker runs in background — failures do not affect capture or API availability

### Toner (TONER) — Fase 8

- [ ] **TONER-01**: Admin can enable SNMP monitoring per printer (opt-in)
- [ ] **TONER-02**: System reads toner level % (black + color if available) via SNMP on schedule
- [ ] **TONER-03**: Toner data displayed as telemetry only — no stock/inventory management
- [ ] **TONER-04**: SNMP failures show last known level or "unavailable" without blocking other features

---

## Phase 5 — Detailed Requirements

**Phase goal:** Establish canonical master data and organization model; link jobs to printers without touching capture hot path; deliver Settings UI.

**Dependencies:** v1.0 shipped (Fases 1–4).  
**Downstream:** Fases 6–8 require Phase 5 complete.

### Phase 5 Acceptance Criteria

| # | Criterion | Maps to |
|---|-----------|---------|
| P5-AC-01 | Admin registers printer with CUPS queue name; new jobs get `printer_id` within 5 min without watcher restart | INV-01, INV-05 |
| P5-AC-02 | Backfill links ≥95% of historical jobs for registered queue names | INV-04 |
| P5-AC-03 | Import 50 users via CSV with 2 invalid rows → 48 created, 2 errors reported | IMPORT-03, IMPORT-04 |
| P5-AC-04 | Stop backend during print → job still captured (watcher independent) | SETTINGS-03, capture invariant |
| P5-AC-05 | Settings UI CRUD works for all four entity types | SETTINGS-01, SETTINGS-02 |
| P5-AC-06 | Department and cost center are independently manageable | ORG-01–06 |
| P5-AC-07 | Audit dashboard `/` still shows jobs with filters after Settings added | SETTINGS-04 |

### Phase 5 Entity Model (requirements-level)

```
Department (1) ──< User (N)
CostCenter (1) ──< Department (N)   [optional FK on department]
CostCenter (1) ──< User (N)         [optional override FK on user]
Printer (N) ──> Department?         [optional location dept]
PrintJob (N) ──> Printer?           [nullable printer_id]
PrintJob.username ──match──> User.cups_username [soft link, no FK required]
```

### Phase 5 API Surface (minimum)

| Method | Path | Requirement |
|--------|------|-------------|
| CRUD | `/api/v1/printers` | INV-01–03, INV-06 |
| CRUD | `/api/v1/departments` | ORG-01–03 |
| CRUD | `/api/v1/cost-centers` | ORG-04–06 |
| CRUD | `/api/v1/users` | ORG-07–09 |
| POST | `/api/v1/import/{entity}` | IMPORT-01–04 |
| GET | `/api/v1/import/templates/{entity}` | IMPORT-05 |
| POST | `/api/v1/admin/backfill-printer-ids` | INV-04 (admin/trigger) |

### Phase 5 Non-Goals (explicit)

- No cost calculation (Fase 6)
- No manager dashboard (Fase 7)
- No fleet/SNMP (Fase 8)
- No LDAP
- No auth/RBAC
- No changes to watcher parse logic except optional import of shared normalize function (shared module, no DB in watcher)

### Phase 5 Technical Constraints

1. Watcher process must not import SQLAlchemy models for org entities
2. `printer_id` assignment must not be in INSERT transaction of watcher
3. Migrations must be reversible (Alembic downgrade tested)
4. Reuse `normalize_printer_name()` from Fase 3 for matching

---

## Phase 5.2 — User–Printer Access Policy

**Phase goal:** Cadastrar política permissiva usuário–impressora, melhorar onboarding de filas na UI e exportar roteiro TI — sem alterar captura nem bloquear impressão.

**Dependencies:** Phase 5 complete (users, printers registry, unmapped-queues).  
**Downstream:** Phase 6 costing may use policy flags in reports; blocking deferred to v2.5 POLICY.

### Phase 5.2 Acceptance Criteria

| # | Criterion | Maps to |
|---|-----------|---------|
| P52-AC-01 | Admin assigns 3 printers to user, marks one default; API returns consistent N:N | ACCESS-01, ACCESS-02 |
| P52-AC-02 | Printer form picks queue from unmapped list; saved printer links jobs as today | ACCESS-04, UX-05-02, INV-01 |
| P52-AC-03 | TI export for user lists display_name, queue, ipp_url, default flag | ACCESS-05 |
| P52-AC-04 | Registered user prints on non-assigned printer → job shows outside-policy indicator; print still completes | ACCESS-05 |
| P52-AC-05 | User with no assignments prints → no block; no false-positive policy flag | permissive model |

### Phase 5.2 Entity Model (requirements-level)

```
User (1) ──< user_printer_access (N) >── Printer (1)
user_printer_access: is_active, is_default (≤1 default per user)
PrintJob ──audit──> printer_id + username ──soft match──> policy check (read-only flag)
```

### Phase 5.2 API Surface (minimum)

| Method | Path | Requirement |
|--------|------|-------------|
| CRUD | `/api/v1/users/{id}/printer-access` | ACCESS-01, ACCESS-02 |
| GET | `/api/v1/printers/{id}/users` (optional) | ACCESS-03 |
| GET | `/api/v1/users/{id}/ti-export` | ACCESS-05 |
| — | Jobs list/export field `outside_policy` | ACCESS-05 |

### Phase 5.2 Non-Goals (explicit)

- No CUPS `pre_process_job` or quota block (v2.5 POLICY)
- No department-level printer inheritance
- No end-user portal to pick printers
- No dashboard authentication (unchanged v1.5)

---

## Future Requirements (v1.6+)

### Policy & Control (v2.5+)

- **POLICY-01**: Quota rules per user/department
- **POLICY-02**: Block print when quota exceeded (requires `pre_process_job` hook)

### Identity (v2.0+)

- **LDAP-01**: Sync users/departments from AD
- **AUTH-01**: Dashboard login with roles

### Production (v3.0)

- **DEPLOY-03**: Full setup-from-zero script
- **DEPLOY-04**: Formal Windows client documentation

---

## Out of Scope

| Feature | Reason |
|---------|--------|
| Billing invoices / accounting export | CHRG = internal only per milestone decision |
| Toner/consumable stock management | Telemetry only |
| LDAP/AD sync | After manual master data stable |
| Print blocking / quotas / CUPS deny | v2.5+ POLICY — 5.2 permissive only |
| Department-level printer access | 5.2 = per-user N:N |
| PostgreSQL | No scale evidence |
| Microservices | Monolith principle |
| Multi-site | Single VM deployment |
| PaperCut enterprise parity | Pragmatic subset |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| ORG-01 – ORG-09 | 5 | Pending |
| INV-01 – INV-06 | 5 | Pending |
| IMPORT-01 – IMPORT-05 | 5 | Pending |
| SETTINGS-01 – SETTINGS-04 | 5 | Pending |
| DATA-04 – DATA-07 | 5 | Pending |
| SERVER-04 | 5 | Complete |
| ACCESS-01 – ACCESS-05 | 5.2 | Pending |
| COST-01 – COST-04 | 6 | Complete |
| CHRG-01 – CHRG-04 | 6 | Complete |
| ANAL-01 – ANAL-05 | 7 | Pending |
| FLEET-01 – FLEET-05 | 8 | Pending |
| TONER-01 – TONER-04 | 8 | Pending |

**Coverage:**
- v1.5 requirements: **52** total (47 + 5 ACCESS)
- Mapped to phases: **52**
- Unmapped: **0** ✓

**Phase 5 subset:** 28 requirements (ORG + INV + IMPORT + SETTINGS + DATA + SERVER-04)  
**Phase 5.2 subset:** 6 requirements (ACCESS-01 – ACCESS-05, UX-05-02)

---
*Requirements defined: 2026-05-27 — ACCESS-01–05 added for Phase 5.2*
