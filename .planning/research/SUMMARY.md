# Project Research Summary — PrintWatch v1.5

**Project:** PrintWatch Management Platform  
**Domain:** Self-hosted operational print management (PME)  
**Researched:** 2026-05-27  
**Confidence:** HIGH

## Executive Summary

v1.5 extends a working audit pipeline with **master data and management layers** without touching the capture hot path. Research confirms: stay on SQLite/monolith/Docker Compose; add Alembic migrations, organization tables, cost calculation on read, and a background fleet scheduler. PaperCut-like UX targets ops managers (registry, costs, dashboards) — not enterprise billing or LDAP day-one.

Key risk: coupling capture to registry. Mitigation: nullable `printer_id`, async matcher, watcher isolation.

## Key Findings

### Recommended Stack

No stack replacement. Add Alembic, optional SNMP library, IPP/ping for fleet. See `STACK.md`.

### Expected Features

**Must have:** Printer registry, dept/user/CC, cost rates, chargeback CSV, manager dashboard, fleet status.  
**Defer:** LDAP, blocking quotas, billing invoices, toner stock.  
See `FEATURES.md`.

### Architecture Approach

Management APIs + new tables in same FastAPI app; fleet as background task; capture unchanged. See `ARCHITECTURE.md`.

### Critical Pitfalls

1. Never block watcher on FK lookups  
2. Normalize CUPS names consistently  
3. SNMP only in background  
4. Cost on aggregated jobs, not raw pages  

See `PITFALLS.md`.

## Implications for Roadmap

### Phase 5: Master Data & Organization
**Rationale:** All downstream features depend on registry.  
**Delivers:** Tables, CRUD APIs, CSV import, Settings UI, printer_id backfill.  
**Avoids:** Capture coupling pitfall.

### Phase 6: Costing & Chargeback
**Rationale:** Requires users/depts/CC/printers linked.  
**Delivers:** Rates, job cost, chargeback export.  
**Avoids:** Double-counting.

### Phase 7: Manager Analytics
**Rationale:** Needs cost dimensions.  
**Delivers:** Manager dashboard, tops, trends.

### Phase 8: Fleet Health & Toner
**Rationale:** Isolated failure domain; optional SNMP.  
**Delivers:** Online/offline, toner telemetry.  
**Avoids:** SNMP in request path.

### Research Flags

- **Phase 5:** Schema design + matcher strategy — discuss before plan
- **Phase 8:** SNMP MIB variance by vendor — spike during plan if needed
- **Phase 6–7:** Standard SQL aggregates — lower research need

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Brownfield |
| Features | HIGH | User + PaperCut reference |
| Architecture | HIGH | Clear separation |
| Pitfalls | HIGH | Known from v1.0 |

**Overall:** HIGH — ready for roadmap.

---
*Research completed: 2026-05-27 — Ready for roadmap: yes*
