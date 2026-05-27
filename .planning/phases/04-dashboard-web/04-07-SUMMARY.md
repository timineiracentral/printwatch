---
phase: 04-dashboard-web
plan: "07"
subsystem: infra
tags: [nginx, docker-compose, vite, multi-stage-build, validate-phase4]

requires:
  - phase: 04-dashboard-web
    plan: "01"
    provides: frontend/ Vite build + dist assets
provides:
  - nginx :80 serving SPA with try_files fallback
  - /api/ reverse proxy to backend:8000 (same-origin DASH-01)
  - scripts/validate-phase4.sh Wave 0 checks
  - .env.example Fase 4 (ALLOWED_ORIGINS, VITE_API_BASE_URL)
affects: [04-06]

tech-stack:
  added: [nginx:1.27-alpine, node:22-alpine multi-stage]
  patterns: [SPA try_files + /api/ proxy_pass; BASE_URL http://localhost]

key-files:
  created:
    - nginx/Dockerfile
    - nginx/default.conf
    - scripts/validate-phase4.sh
    - .dockerignore
  modified:
    - docker-compose.yml
    - .env.example
    - backend/Dockerfile

key-decisions:
  - "API acessível só via nginx :80 — sem ports 8000 no backend (D-56)"
  - "VITE_API_BASE_URL vazio em prod — same-origin /api/v1 (D-40)"
  - "ALLOWED_ORIGINS inclui localhost:5173 e localhost para dev + nginx (D-58)"

patterns-established:
  - "validate-phase4.sh: BASE_URL default http://localhost (nginx), não :8000"
  - "nginx default.conf: gzip + cache immutable em *.js/*.css (D-63)"

requirements-completed: [DASH-01]

duration: 25min
completed: 2026-05-27
---

# Phase 4 Plan 07: nginx :80 + API Proxy Summary

**Deploy nginx na porta 80 com build multi-stage do frontend React, proxy `/api/` para o backend sem expor :8000 no host, e script `validate-phase4.sh` para Wave 0 Nyquist.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-05-27T13:40:00Z
- **Completed:** 2026-05-27T14:05:00Z
- **Tasks:** 1
- **Files modified:** 7

## Accomplishments

- `nginx/Dockerfile` multi-stage: `npm ci && npm run build` → `nginx:1.27-alpine` com `dist/`
- `nginx/default.conf`: `try_files` SPA, `proxy_pass http://backend:8000/api/`, gzip e cache immutable
- Serviço `nginx` no `docker-compose.yml` (`80:80`, `depends_on: backend`)
- `scripts/validate-phase4.sh --quick`: health, jobs, stats, printers, export CSV, Vitest
- `.env.example` atualizado com `ALLOWED_ORIGINS`, `API_TIMEZONE`, `VITE_API_BASE_URL`

## Task Commits

1. **Task 1: nginx multi-stage + docker-compose + validate-phase4.sh** - `34e10fe` (feat)

## Files Created/Modified

- `nginx/Dockerfile` - Build frontend + imagem nginx final
- `nginx/default.conf` - SPA + proxy API + gzip/cache
- `docker-compose.yml` - Serviço nginx; `ALLOWED_ORIGINS`/`API_TIMEZONE` no backend
- `scripts/validate-phase4.sh` - Validação Wave 0 via `BASE_URL=http://localhost`
- `.env.example` - Variáveis Fase 4
- `.dockerignore` - Exclui `node_modules` e artefatos do contexto de build
- `backend/Dockerfile` - `sed` remove CRLF do entrypoint (build Windows)

## Decisions Made

- Backend permanece sem `ports: 8000:8000` — API só via nginx ou `docker compose exec`
- Checks gzip/cache em JS são WARN (dependem de `Accept-Encoding` do cliente)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] CRLF no `backend/entrypoint.sh` após rebuild**
- **Found during:** Verificação `docker compose up --build nginx`
- **Issue:** Backend em loop `exec ... no such file or directory`; nginx retornava 502 no `/api/`
- **Fix:** `RUN sed -i 's/\r$//' /usr/local/bin/entrypoint.sh` no `backend/Dockerfile`
- **Files modified:** `backend/Dockerfile`
- **Verification:** `curl http://localhost/api/v1/health` → `{"status":"ok",...}`
- **Committed in:** `34e10fe`

**2. [Rule 2 - Missing Critical] `ALLOWED_ORIGINS`/`API_TIMEZONE` no compose backend**
- **Found during:** Task 1 (alinhamento D-58 com `.env.example`)
- **Issue:** Compose não repassava origens para CORS em dev/nginx
- **Fix:** Bloco `environment` no serviço `backend` com defaults documentados
- **Files modified:** `docker-compose.yml`
- **Committed in:** `34e10fe`

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 missing critical)
**Impact on plan:** Necessários para stack E2E funcional no ambiente Windows; sem mudança de escopo DASH-01.

## Issues Encountered

- `bash scripts/validate-phase4.sh` indisponível no host (WSL/bash ausente); verificação equivalente feita com `curl.exe` + `npm test -- --run` (12 testes OK)
- Porta 80 já em uso em alguns ambientes — documentar conflito local se `docker compose up nginx` falhar no bind

## User Setup Required

- Copiar `.env.example` → `.env` e ajustar `ALLOWED_NETWORK`, credenciais CUPS e `http://VM_HOST` nas origens CORS
- Subir stack: `docker compose up -d --build nginx`
- Validar: `bash scripts/validate-phase4.sh --quick` (Linux/macOS/Git Bash)

## Next Phase Readiness

- DASH-01 infra pronta — planos 04-02–04-06 podem consumir same-origin `/api/v1`
- Plan 04-06 pode expandir `validate-phase4.sh` com paridade total da fase 3 + checkpoint humano

## Self-Check: PASSED

- FOUND: nginx/Dockerfile
- FOUND: nginx/default.conf
- FOUND: scripts/validate-phase4.sh
- FOUND: commit 34e10fe
- VERIFIED: `curl http://localhost/` contém `<div id="root">`
- VERIFIED: `curl http://localhost/api/v1/health` status ok
- VERIFIED: `docker compose config` sem publish 8000 no backend

---
*Phase: 04-dashboard-web*
*Completed: 2026-05-27*
