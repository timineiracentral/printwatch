---
phase: 01-infrastructure-print-server
plan: 05
subsystem: infra
tags: [vm-deploy, bootstrap, docker, cups, runbook, VM_HOST]

requires:
  - phase: 01-03
    provides: "setup-printer.sh, vm-setup.md, validate-phase1.sh"
provides:
  - "scripts/bootstrap-vm.sh idempotente (Docker + compose + impressora + smoke)"
  - "scripts/verify-vm-network.sh (631, ACL, ufw warn)"
  - "docs/vm-deploy-runbook.md sequência operacional VM printwatch"
  - "VM VM_HOST com CUPS operacional e test_printer (evidência operador)"
affects: [01-04]

tech-stack:
  added: [bootstrap-vm.sh, verify-vm-network.sh]
  patterns:
    - "Docker CE existente: skip apt docker.io em conflito containerd"
    - "Guard .env changeme antes de compose up"
    - "[PASS]/[FAIL]/[WARN] alinhado a validate-phase1.sh"

key-files:
  created:
    - scripts/bootstrap-vm.sh
    - scripts/verify-vm-network.sh
    - docs/vm-deploy-runbook.md
  modified:
    - docs/vm-setup.md

key-decisions:
  - "bootstrap-vm.sh não força apt docker.io quando Docker CE + compose já funcionam"
  - "Conflito containerd.io documentado no runbook — manter Docker CE pré-instalado"
  - "Checkpoint Task 3 aprovado com evidência manual 2026-05-26 (operador)"

patterns-established:
  - "Deploy VM: bootstrap-vm.sh → verify-vm-network.sh → gate phase1-validation"
  - "Runbook separa preparação manual (vm-setup) vs deploy automatizado"

requirements-completed: [DEPLOY-01, SERVER-01, SERVER-03]

duration: 25min
completed: 2026-05-26
---

# Phase 01 Plan 05: VM Deploy Bootstrap Summary

**Bootstrap e runbook para VM printwatch (VM_HOST) com CUPS em produção — desbloqueia validação IPP remota 01-04**

## Performance

- **Duration:** 25 min
- **Started:** 2026-05-26T18:00:00Z
- **Completed:** 2026-05-26T18:25:00Z
- **Tasks:** 3 (2 auto + 1 checkpoint aprovado)
- **Files modified:** 4

## Accomplishments

- `scripts/bootstrap-vm.sh` automatiza Docker (com skip inteligente), `.env` guard, `compose up`, wait CUPS, setup-printer e `validate --quick`
- `scripts/verify-vm-network.sh` valida container, HTTP :631, porta publicada, ACL e ufw opcional
- `docs/vm-deploy-runbook.md` documenta sequência operacional e troubleshooting containerd
- **VM deploy confirmado** pelo operador em 2026-05-26 — bloqueio B-01-04-VM resolvido

## Task Commits

Each task was committed atomically:

1. **Task 1: Criar scripts/bootstrap-vm.sh idempotente** - `cbb27f3` (feat)
2. **Task 2: Criar verify-vm-network.sh e runbook** - `0232fb5` (feat)
3. **Task 3: Checkpoint deploy VM** - aprovado (evidência operador; sem commit de código)

**Plan metadata:** pendente neste commit (docs)

## VM Deploy Evidence (Task 3 — Approved)

**Data:** 2026-05-26  
**Operador:** deploy manual na VM, checkpoint aprovado com evidência fornecida.

| Item | Resultado |
|------|-----------|
| SSH | `admin-user@VM_HOST` — Ubuntu 22.04.5 LTS |
| Hostname | `printwatch` |
| IP | `VM_HOST/24` em eth0 |
| Docker | Compose v5.1.3 (Docker CE pré-instalado); `apt docker.io` falhou por conflito containerd |
| Deploy | `git clone` + `cp .env.example .env` + edit; `docker compose up -d --build` SUCCESS |
| Container | `printwatch-cups-1` running, `0.0.0.0:631->631/tcp` |
| Impressora | `./scripts/setup-printer.sh` → `test_printer` → `ipp://PRINTER_HOST/ipp/print` (everywhere) |
| lpstat | impressora enabled |
| Smoke | `bash scripts/validate-phase1.sh --quick` → **0 FAIL, 0 WARN, 17 PASS** |

**Próximo passo:** retomar **01-04 Task 3** — job remoto IPP desde Windows ([phase1-validation.md §2](../../docs/phase1-validation.md)).

## Files Created/Modified

- `scripts/bootstrap-vm.sh` — Bootstrap idempotente na VM com flags `--skip-docker-install` e `--dry-run`
- `scripts/verify-vm-network.sh` — Checks rede 631, ACL, ufw warn, hint curl remoto
- `docs/vm-deploy-runbook.md` — Runbook PT-BR com gate de prontidão e troubleshooting containerd
- `docs/vm-setup.md` — Link para runbook; distinção manual vs automatizado

## Decisions Made

- Preferir Docker CE existente sobre `apt install docker.io` quando há conflito com `containerd.io`
- Checkpoint humano documentado por evidência — scripts criados localmente, execução validada na VM real

## Deviations from Plan

None — plan executed as written. Operador usou passos manuais equivalentes ao runbook antes dos scripts existirem; scripts espelham o que foi feito.

## Auth Gates

None.

## Threat Flags

Omitido — nenhuma superfície nova além do previsto no threat_model (bootstrap sem auto-sudo, .env guard changeme).

## Self-Check: PASSED

- FOUND: scripts/bootstrap-vm.sh
- FOUND: scripts/verify-vm-network.sh
- FOUND: docs/vm-deploy-runbook.md
- FOUND: docs/vm-setup.md (modified)
- FOUND: cbb27f3
- FOUND: 0232fb5

---
*Phase: 01-infrastructure-print-server*
*Plan: 05 — VM deploy bootstrap*
