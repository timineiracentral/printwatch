# Feature Research — PrintWatch v1.5

**Domain:** Operational print management (PME / self-hosted)  
**Researched:** 2026-05-27  
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Printer registry | PaperCut always has device list | MEDIUM | Replace DISTINCT `/printers` |
| Department assignment | Chargeback by org unit | MEDIUM | Manual + CSV before LDAP |
| Cost per page mono/color | Manager asks "how much?" | MEDIUM | Global rates first |
| Usage by department | Budget accountability | MEDIUM | Requires master data |
| Printer online status | Ops visibility | MEDIUM | CUPS/IPP + ping hybrid |
| Settings/admin UI | Can't config via API only | MEDIUM | New nav section |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Self-hosted monolith | No cloud lock-in | LOW | Already v1.0 |
| Cost center ≠ department | Real accounting structure | LOW | User-confirmed |
| Non-blocking capture | Print always works | LOW | Architectural invariant |
| Hybrid fleet check | Works without full SNMP | MEDIUM | Pragmatic vs enterprise agents |

### Anti-Features (Commonly Requested, Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Real-time billing invoices | Finance wants bills | Scope explosion | Internal CSV chargeback |
| Toner inventory/stock | Supply management | Different product | SNMP level % only |
| LDAP day-one | AD integration | Unstable username mapping | CSV import first |
| Agent on every PC | Rich telemetry | Breaks simple CUPS model | Server-side logs only |
| Blocking print for quota | Cost control | Violates core value | Report-only v1.5 |

## Feature Dependencies

```
Printer Registry
    └──requires──> Department/CC (optional metadata)
User Registry
    └──requires──> Department
Cost Calculation
    └──requires──> Cost Rates + Print Jobs + User/Printer links
Chargeback Reports
    └──requires──> Cost Calculation
Manager Dashboard
    └──requires──> Cost + Organization dimensions
Fleet Online Status
    └──requires──> Printer Registry (IP, CUPS queue name)
Toner Telemetry
    └──requires──> Printer Registry + SNMP opt-in flag
```

## MVP Definition (v1.5)

### Launch With

- [ ] Printer CRUD + CUPS queue mapping — foundation
- [ ] Departments, users, cost centers + CSV import
- [ ] Cost rates + job cost + dept chargeback CSV
- [ ] Manager dashboard (consumption/cost tops)
- [ ] Fleet status + optional toner %

### Add After Validation (v1.6+)

- [ ] Per-printer cost rate overrides
- [ ] Scheduled email reports
- [ ] LDAP sync

### Future (v2.0+)

- [ ] Policies/quotas with blocking
- [ ] Auth/RBAC

## Feature Prioritization Matrix

| Feature | User Value | Cost | Priority |
|---------|------------|------|----------|
| Master data | HIGH | MEDIUM | P1 (Fase 5) |
| Costing/chargeback | HIGH | MEDIUM | P1 (Fase 6) |
| Manager analytics | HIGH | MEDIUM | P1 (Fase 7) |
| Fleet/toner | MEDIUM | MEDIUM | P2 (Fase 8) |
| Per-printer rates | MEDIUM | LOW | P3 (defer) |

## Competitor Feature Analysis

| Feature | PaperCut | PrintWatch v1.5 |
|---------|----------|-----------------|
| Printer registry | Full + SNMP | CRUD + CUPS link + optional SNMP |
| Chargeback | Full billing | Internal CSV/reports |
| Departments | AD sync | Manual + CSV |
| Fleet | Advanced | CUPS/IPP + ping + toner opt-in |

---
*Feature research for: v1.5 Management Platform*
