# Architecture Research — PrintWatch v1.5

**Researched:** 2026-05-27  
**Confidence:** HIGH (brownfield extension)

## Existing Architecture

```
[Windows Clients] --IPP--> [CUPS container] --page_log-->
                                |
                    [Watcher process] --append--> [SQLite print_jobs]
                                |
                    [FastAPI backend] <--read/query-- [React dashboard]
                                |
                    [nginx :80]
```

**Invariant:** Capture path has no dependency on master data tables.

## v1.5 Architecture (target)

```
                    ┌─────────────────────────────────────┐
                    │           FastAPI Monolith           │
                    │  ┌─────────┐  ┌──────────────────┐  │
                    │  │ Capture │  │ Management APIs  │  │
                    │  │ (read)  │  │ CRUD org/printer │  │
                    │  └────┬────┘  └────────┬─────────┘  │
                    │       │                │             │
                    │  ┌────▼────────────────▼─────────┐  │
                    │  │     SQLAlchemy / SQLite        │  │
                    │  │ print_jobs | printers | users  │  │
                    │  └────────────────────────────────┘  │
                    │  ┌────────────────────────────────┐  │
                    │  │ FleetScheduler (background)    │  │
                    │  │ CUPS/IPP → ping → SNMP toner   │  │
                    │  └────────────────────────────────┘  │
                    └─────────────────────────────────────┘
[Watcher] ──append only──> print_jobs (printer string + optional printer_id)
```

## New Components

| Component | Responsibility | Phase |
|-----------|----------------|-------|
| `printers` table + API | Canonical device; `cups_queue_name`, IP, metadata | 5 |
| `departments`, `cost_centers`, `users` | Organization model | 5 |
| `printer_matcher` | Backfill/link `printer_id` on jobs (async/batch) | 5 |
| `cost_rates` + cost calculator | Derive cost from pages × rate × color | 6 |
| `stats/manager` endpoints | Aggregations by org dimension | 7 |
| `fleet_checker` | Periodic CUPS/IPP/ping | 8 |
| `snmp_reader` | Opt-in toner levels | 8 |
| Settings UI routes | React pages under `/settings/*` | 5+ |

## Data Flow Changes

### Job ingest (unchanged hot path)

1. Watcher parses line → INSERT `print_jobs` with `printer` string (as today)
2. **No FK required at insert** — `printer_id` nullable
3. Matcher job (cron/startup): `UPDATE print_jobs SET printer_id = ? WHERE printer = ? AND printer_id IS NULL`

### Read path enrichment

- API joins `printers` / `users` when `printer_id` or username match exists
- Unmapped jobs still visible (audit dashboard unchanged)

## Integration Points

| System | Integration | Failure mode |
|--------|-------------|--------------|
| CUPS | `lpstat -p`, IPP Get-Printer-Attributes | Mark unknown; don't block print |
| Printer IP | ICMP ping | Fallback only |
| SNMP | UDP 161, printer MIB | Skip if disabled; store last reading |

## Build Order (phases)

1. **Schema + CRUD** — entities before calculations
2. **Linking** — backfill printer_id, user dept
3. **Costing** — rates + computed fields on read or materialized view
4. **Analytics** — new dashboard routes
5. **Fleet** — background scheduler last (isolated failure domain)

## New vs Modified

| New | Modified |
|-----|----------|
| 6+ tables | `print_jobs.printer_id` nullable FK |
| Settings UI | Existing audit dashboard (add nav) |
| Manager dashboard | `/stats/summary` extend or parallel |
| Fleet scheduler | `main.py` lifespan |
| — | `/printers` deprecate → registry API |

---
*Architecture research for: v1.5 Management Platform*
