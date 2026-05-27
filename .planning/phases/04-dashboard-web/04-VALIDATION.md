---
phase: 4
slug: dashboard-web
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-27
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest ^3.x + @testing-library/react (Wave 0 — não existe ainda) |
| **Config file** | `frontend/vitest.config.ts` (criar) |
| **Quick run command** | `cd frontend && npm test -- --run` |
| **Full suite command** | `bash scripts/validate-phase4.sh --quick` + `npm test` |
| **Estimated runtime** | ~30–60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm test -- --run` (quando existir)
- **After every plan wave:** Run `bash scripts/validate-phase4.sh --quick`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | DASH-01 | T-04-01 / — | nginx serve SPA; proxy /api/ sem expor backend na rede host | integration | `curl -sf http://localhost/` ; `curl -sf http://localhost/api/v1/health` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 2 | DASH-04 | T-04-02 / — | Filtros round-trip URL ↔ params; sem XSS em render | unit | Vitest `filtersToSearchParams` / `parseFiltersFromUrl` | ❌ W0 | ⬜ pending |
| 04-03-01 | 03 | 2 | DASH-02 | — | Cards usam stats API; não recalcular tops | integration | `curl -sf http://localhost/api/v1/stats/summary` | ❌ W0 | ⬜ pending |
| 04-04-01 | 04 | 2 | DASH-03 | — | Paginação server-side page/size | unit+integration | Vitest + `curl /api/v1/jobs?page=1&size=50` | ❌ W0 | ⬜ pending |
| 04-05-01 | 05 | 2 | DASH-05 | — | Debounce 300ms em search | unit | Vitest fake timers | ❌ W0 | ⬜ pending |
| 04-06-01 | 06 | 3 | EXPORT-01 | — | CSV com filtros ativos; 400 em cap 100k | integration | curl export headers (espelhar validate-phase3) | ❌ W0 | ⬜ pending |
| 04-07-01 | 07 | 3 | DASH-06 | — | Shell <2s rede local | manual | checkpoint humano ROADMAP crit. 1 | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/` scaffold Vite React-TS + Tailwind v4 (`@tailwindcss/vite`)
- [ ] `frontend/vitest.config.ts` + testes `lib/filters.ts`, `lib/dates.ts`, `lib/media.ts`
- [ ] `scripts/validate-phase4.sh` — nginx up, `/` 200, `/api/v1/health`, jobs/stats shape, export headers
- [ ] `nginx/Dockerfile` + `default.conf` (try_files + proxy_pass)
- [ ] `docker-compose.yml` serviço `nginx` (porta 80)
- [ ] `.env.example`: `ALLOWED_ORIGINS`, `VITE_API_BASE_URL` (opcional)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dashboard abre <2s na rede local | DASH-06 | Percepção + rede VM | Browser em `http://<VM_HOST>`; DevTools Network; validar cards+tabela |
| Cards batem com banco | DASH-02 | Comparação SQL | Checkpoint: `stats.hoje.jobs` vs `SELECT COUNT(*) ...` |
| Filtro usuário+impressora | DASH-04 | UX visual | Aplicar filtros; conferir tabela vs API |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
