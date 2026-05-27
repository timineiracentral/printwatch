# Stack Research — PrintWatch v1.5

**Domain:** Print management / MPS (managed print services) brownfield extension  
**Researched:** 2026-05-27  
**Confidence:** HIGH (brownfield — stack mostly fixed)

## Existing Stack (unchanged)

| Layer | Technology | v1.5 role |
|-------|------------|-----------|
| Print | CUPS 2.4+ | Source of truth for queue status (fleet) |
| Capture | Python watchdog | **Untouched** — append-only ingest |
| DB | SQLite + SQLAlchemy | New tables + Alembic migrations |
| API | FastAPI | New `/api/v1` routes for master data |
| UI | React + Vite + Tailwind v4 | Settings area + future manager views |
| Deploy | Docker Compose + nginx | Same topology |

## Additions for v1.5

| Addition | Purpose | Rationale |
|----------|---------|-----------|
| **Alembic** | Schema migrations | Master data needs versioned DDL; avoid raw SQL scripts |
| **pydantic-settings** | Already in use | Extend for SNMP/fleet env vars |
| **pysnmp-lextudio** or **easysnmp** | SNMP toner (opt-in) | Industry standard for printer MIBs; lazy import per printer |
| **httpx** or **requests** | IPP health checks | Async-friendly IPP queries from backend |
| **subprocess ping** or **icmplib** | IP fallback | Simple reachability when CUPS queue stale |

## What NOT to add

| Avoided | Reason |
|---------|--------|
| PostgreSQL | No scale evidence; SQLite fine for 20–100 users |
| Redis/Celery | Background fleet checks = APScheduler in-process or FastAPI lifespan |
| GraphQL | REST consistent with v1.0 |
| Separate admin service | Monolith principle |
| LDAP libraries | Deferred milestone |
| TimescaleDB/OLAP | Analytics via SQL aggregates on SQLite |

## Integration points

1. **Watcher → DB:** Continues writing `print_jobs` only; optional `printer_id` resolved async/post-insert or via trigger-free application layer on read (prefer: nullable FK filled by background matcher, never block insert).
2. **Backend → CUPS:** Read-only `lpstat` / IPP for queue state (fleet phase); no write path in capture hot path.
3. **Backend → SNMP:** Separate scheduled task; timeout per device; failures = last-known status.

## Versions

- Python 3.11+ (existing Dockerfile)
- SQLAlchemy 2.x (existing)
- React 19 / Vite 6 (existing frontend)
- Alembic: latest compatible with SQLAlchemy 2

## Sources

- Existing `backend/`, `frontend/`, `docker-compose.yml`
- PaperCut NG feature subset (operational, not enterprise)
- CUPS IPP documentation (queue status)

---
*Stack research for: v1.5 Management Platform*
