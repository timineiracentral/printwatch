---
phase: 01
slug: infrastructure-print-server
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-26
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Bash smoke tests (sem pytest/jest — greenfield infra) |
| **Config file** | `scripts/validate-phase1.sh` (Wave 0) |
| **Quick run command** | `bash scripts/validate-phase1.sh --quick` |
| **Full suite command** | `bash scripts/validate-phase1.sh` |
| **Estimated runtime** | ~30 seconds (quick) / ~90 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run `docker compose exec -T cups cupsd -t`
- **After every plan wave:** Run `bash scripts/validate-phase1.sh --quick`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | DEPLOY-02 | — | `.env.example` documents ALLOWED_NETWORK + CUPS admin placeholders | unit | `grep -E 'ALLOWED_NETWORK\|CUPS_ADMIN' .env.example` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 2 | SERVER-02 | T-01-01 | PageLogFormat non-empty in cupsd.conf | smoke | `docker compose exec -T cups grep PageLogFormat /etc/cups/cupsd.conf` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 2 | DEPLOY-01 | — | Compose starts without error | smoke | `docker compose up -d --build && docker compose ps` | ❌ W0 | ⬜ pending |
| 01-02-03 | 02 | 2 | SERVER-01 | T-01-02 | ACL REDACTED_IP/16 in generated cupsd.conf | smoke | `docker compose exec -T cups grep 'Allow from REDACTED_IP/16' /etc/cups/cupsd.conf` | ❌ W0 | ⬜ pending |
| 01-02-04 | 02 | 2 | DEPLOY-01 | — | cupsd config valid | smoke | `docker compose exec -T cups cupsd -t` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 3 | SERVER-03 | — | Test printer registered | smoke | `docker compose exec -T cups lpstat -p $TEST_PRINTER_NAME` | ❌ W0 | ⬜ pending |
| 01-04-01 | 04 | 4 | SERVER-02 | — | page_log receives line after local job | integration | `bash scripts/validate-phase1.sh` | ❌ W0 | ⬜ pending |
| 01-04-02 | 04 | 4 | SERVER-01 | T-01-02 | Remote IPP from REDACTED_LAN (checkpoint) | manual | Print from Windows PC; verify page_log | ❌ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `scripts/validate-phase1.sh` — smoke tests for DEPLOY-01, SERVER-01, SERVER-02, SERVER-03
- [ ] `scripts/setup-printer.sh` — idempotent lpadmin wrapper
- [ ] `cups/Dockerfile` + `entrypoint.sh` + `cupsd.conf.template` + `cups-files.conf`
- [ ] `docker-compose.yml` + `.env.example`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| ACL blocks non-REDACTED_LAN | SERVER-01 | Requires second network segment | curl :631 from IP outside REDACTED_IP/16 → expect 403 |
| Remote IPP job from Windows | D-13 mode 2 | Requires Windows client on LAN | Add printer IPP URL; print test page; verify page_log line with printer name + timestamp |
| Username `DOMINIO\usuario` in page_log | D-14 | Windows IPP behavior varies | Compare page_log user field after Windows job vs expected AD format |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 90s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
