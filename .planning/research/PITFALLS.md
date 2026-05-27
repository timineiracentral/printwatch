# Pitfalls Research — PrintWatch v1.5

**Researched:** 2026-05-27  
**Confidence:** HIGH

## Critical Pitfalls

### 1. Blocking capture on master data lookups

**Warning signs:** Watcher imports org models; INSERT waits on printer FK resolution.  
**Prevention:** Watcher code path must not import management modules; `printer_id` filled asynchronously.  
**Phase:** 5 — enforce in plan review.

### 2. CUPS queue name drift

**Warning signs:** Jobs under `HP_2F_Piso2` but registry has `hp-piso2`.  
**Prevention:** `normalize_printer_name()` reuse from Fase 3; explicit `cups_queue_name` on Printer; matcher uses same function.  
**Phase:** 5.

### 3. Username ↔ User registry mismatch

**Warning signs:** AD usernames change format; orphan jobs.  
**Prevention:** User keyed by exact CUPS username; import CSV documents format; unassigned bucket in reports.  
**Phase:** 5–6.

### 4. SNMP slowing API

**Warning signs:** Sync SNMP in request handler; dashboard timeouts.  
**Prevention:** Background scheduler only; cache `printer_health` table; API reads cache.  
**Phase:** 8.

### 5. Cost double-counting

**Warning signs:** Summing page rows AND job aggregates.  
**Prevention:** Cost API uses same aggregation as `/jobs` (group by job_id); document in API.  
**Phase:** 6.

### 6. SQLite write contention

**Warning signs:** Fleet checker + watcher + bulk backfill lock DB.  
**Prevention:** Batch updates off-peak; WAL mode; short transactions; backfill chunked.  
**Phase:** 5, 8.

### 7. Scope creep to PaperCut parity

**Warning signs:** Follow-me, secure release, driver store in v1.5 plans.  
**Prevention:** REQUIREMENTS Out of Scope; phase verifier checks.  
**Phase:** All.

## Integration Pitfalls

| Pitfall | Prevention |
|---------|------------|
| CUPS container unreachable from backend | Share network in compose; document `CUPS_HOST` |
| Ping blocked by firewall | IPP status still works; show "unreachable" not error |
| SNMP community string security | Env var; read-only community; opt-in per printer |

## Recovery Strategies

- Fleet check failure → last known status + timestamp
- Import CSV validation errors → row-level errors, partial commit option
- Migration failure → Alembic downgrade path documented

---
*Pitfalls research for: v1.5 Management Platform*
