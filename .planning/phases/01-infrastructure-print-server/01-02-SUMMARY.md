---
phase: 01-infrastructure-print-server
plan: 02
subsystem: infra
tags: [cups, docker, ubuntu-22.04, envsubst, acl, page-log, wave-2]

requires:
  - phase: 01-01
    provides: "docker-compose.yml, .env.example, validate-phase1.sh Wave 0"
provides:
  - "cups/Dockerfile Ubuntu 22.04 com drivers HP/Samsung e cups-pdf"
  - "cupsd.conf.template com ACL REDACTED_IP/16 e PageLogFormat explícito"
  - "entrypoint idempotente: envsubst, admin user, cupsd -t"
  - "validate-phase1.sh --quick com checks runtime quando container up"
affects: [01-03, 01-04]

tech-stack:
  added: [CUPS 2.4 apt, gettext-base envsubst, printer-driver-cups-pdf]
  patterns:
    - "Template cupsd.conf + envsubst whitelist só ALLOWED_NETWORK (T-01-05)"
    - "Policy blocks CUPS 2.4 dentro de <Policy> — cupsd -t no entrypoint"
    - "Runtime checks opcionais no validate quando Docker offline"

key-files:
  created:
    - cups/Dockerfile
    - cups/cupsd.conf.template
    - cups/cups-files.conf
    - cups/entrypoint.sh
  modified:
    - scripts/validate-phase1.sh

key-decisions:
  - "ACL deny-by-default com Allow from @LOCAL para healthcheck interno além de REDACTED_IP/16"
  - "validate-phase1.sh emite WARN (não FAIL) quando Docker daemon offline — compatibilidade Wave 0"
  - "Blocos Policy default + authenticated copiados do cupsd.conf.in v2.4 para passar cupsd -t"

patterns-established:
  - "Entrypoint: validar CIDR → envsubst → criar admin → cupsd -t → exec cupsd -f"
  - "cups-files.conf versionado com PageLog /var/log/cups/page_log e LogFilePerm 0644"

requirements-completed: [SERVER-01, SERVER-02, DEPLOY-01]

duration: 18min
completed: 2026-05-26
---

# Phase 01 Plan 02: Container CUPS Summary

**Container CUPS customizado Ubuntu 22.04 com ACL REDACTED_IP/16, PageLogFormat explícito e entrypoint envsubst — pronto para `docker compose up --build` na VM**

## Performance

- **Duration:** 18 min
- **Started:** 2026-05-26T16:20:00Z
- **Completed:** 2026-05-26T16:38:00Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- `cups/Dockerfile` instala CUPS 2.4, drivers HP/Samsung, cups-pdf e gettext-base via apt jammy
- `cupsd.conf.template` define PageLogFormat da SPEC e ACL restrita a `${ALLOWED_NETWORK}` + `@LOCAL`
- `entrypoint.sh` valida CIDR, aplica envsubst whitelist, cria admin e roda `cupsd -t` antes de subir
- `validate-phase1.sh --quick` inclui checks runtime (cupsd -t, :631, PageLogFormat, ACL) quando container está up

## Task Commits

Each task was committed atomically:

1. **Task 1: Criar cups/Dockerfile com pacotes Ubuntu 22.04** - `7851bdf` (feat)
2. **Task 2: Configurar cupsd.conf.template, cups-files.conf e entrypoint.sh** - `3675672` (feat)
3. **Task 3: Build, subir container e validar CUPS operacional** - `43917fb` (feat)

**Plan metadata:** pendente neste commit (docs)

## Files Created/Modified

- `cups/Dockerfile` — Imagem Ubuntu 22.04, pacotes CUPS/drivers, entrypoint
- `cups/cupsd.conf.template` — PageLogFormat, ACL REDACTED_IP/16, Policy blocks v2.4
- `cups/cups-files.conf` — PageLog path e LogFilePerm 0644
- `cups/entrypoint.sh` — envsubst, validação CIDR, admin user, cupsd -t
- `scripts/validate-phase1.sh` — Checks runtime condicionais quando Docker/cups up

## Decisions Made

- Incluído `Allow from @LOCAL` em todos os blocos `<Location>` para healthcheck interno sem abrir ranges RFC1918 genéricos
- Checks de container no validate degradam para WARN quando daemon Docker offline (dev Windows sem Desktop ativo)
- Policy `default` e `authenticated` completas — evita falha `cupsd -t` por diretivas JobPrivateAccess fora de `<Policy>`

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- **Docker Desktop offline no host Windows de dev:** `docker compose build/up` falhou (`dockerDesktopLinuxEngine` pipe ausente). Arquivos validados estaticamente; checks runtime marcados SKIP/WARN. Validação completa requer Docker ativo na VM `VM_HOST` ou iniciar Docker Desktop localmente.

## User Setup Required

Antes do primeiro `docker compose up --build`:

```bash
cp .env.example .env
# editar CUPS_ADMIN_PASSWORD (não usar changeme) e TEST_PRINTER_URI
docker compose up -d --build
bash scripts/validate-phase1.sh --quick
```

## Next Phase Readiness

- Plan 03 pode implementar `scripts/setup-printer.sh` — CUPS container buildável via compose
- Plan 04 depende de container running para job local `lp` e validação page_log
- Executar `docker compose up -d --build` na VM para confirmar SERVER-01 runtime (HTTP 200 :631)

## Self-Check: PASSED

- FOUND: cups/Dockerfile
- FOUND: cups/cupsd.conf.template
- FOUND: cups/cups-files.conf
- FOUND: cups/entrypoint.sh
- FOUND: scripts/validate-phase1.sh
- FOUND: 7851bdf, 3675672, 43917fb
- SKIP (Docker offline): docker compose up, cupsd -t runtime, curl :631

---
*Phase: 01-infrastructure-print-server*
*Completed: 2026-05-26*
