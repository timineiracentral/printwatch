---
phase: 01-infrastructure-print-server
verified: 2026-05-26T20:00:00Z
status: human_needed
score: 7/10 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Na VM (SSH VM_HOST), executar `bash scripts/validate-phase1.sh` (modo full, sem --quick) e confirmar exit 0 com job local lp + linha no page_log"
    expected: "Exit 0; última linha de page_log passa PAGE_LOG_REGEX; printer == test_printer; username contém backslash"
    why_human: "Verificador não conseguiu executar bash na VM (SSH batch negado; WSL indisponível no host Windows)"
  - test: "De um PC Windows na rede REDACTED_LAN, imprimir página de teste via IPP `http://VM_HOST:631/printers/test_printer` e inspecionar page_log na VM"
    expected: "Nova linha em page_log com test_printer, username AD (ex.: DOMAIN\usuario), timestamp recente; impressão física na HP/Samsung"
    why_human: "Job remoto IPP é checkpoint humano (D-13.2); evidência existe apenas em SUMMARY 01-04, não no repositório"
  - test: "De outro host REDACTED_LAN (não a VM), executar `curl -s -o /dev/null -w '%{http_code}' http://VM_HOST:631/`"
    expected: "HTTP 200 — confirma SERVER-01 (CUPS acessível na LAN, não só localhost)"
    why_human: "ACL configurada no template; acesso remoto LAN não verificável programaticamente pelo verificador"
  - test: "Confirmar que `TEST_PRINTER_URI` na VM usa porta :631 no backend (ex.: ipp://PRINTER_HOST:631/ipp/print) e reimprimir do Windows"
    expected: "Impressão física confirmada após URI correta (troubleshooting Seção 5 de phase1-validation.md)"
    why_human: "Terminal mostra tentativa socket:// com falha; correção IPP :631 em andamento — estado final não auditável no repo"
---

# Fase 1: Infrastructure & Print Server — Relatório de Verificação

**Objetivo da fase:** VM Ubuntu 22.04 com Docker Compose funcionando e CUPS recebendo jobs de teste via IPP — base da cadeia de impressão.

**Verificado:** 2026-05-26T20:00:00Z  
**Status:** human_needed  
**Re-verificação:** Não — verificação inicial

## Nota MVP

A fase está marcada `mode: mvp` no ROADMAP, mas o **goal da fase** não está no formato user story (`As a …, I want …, so that ….`). Apenas o plano 01-01 declara user story parcial. A cobertura de fluxo abaixo deriva do objetivo operacional (D-01–D-22) e dos critérios de sucesso do ROADMAP.

## User Flow Coverage

Fluxo alvo: **admin de TI → compose up → impressora cadastrada → job IPP → page_log válido**

| Etapa | Esperado | Evidência no codebase | Status |
|-------|----------|----------------------|--------|
| Subir stack | `docker compose up -d --build` sobe só CUPS | `docker-compose.yml` (serviço `cups`, volumes, porta 631); `scripts/bootstrap-vm.sh` | ✓ VERIFIED |
| Configurar rede CUPS | ACL REDACTED_IP/16, deny-by-default | `cups/cupsd.conf.template` + `cups/entrypoint.sh` (envsubst) | ✓ VERIFIED |
| Cadastrar impressora | Script idempotente lpadmin | `scripts/setup-printer.sh` → `docker compose exec … lpadmin` | ✓ VERIFIED |
| Job local (sanidade) | `lp` no container → page_log | `scripts/validate-phase1.sh` modo full (automático) | ? UNCERTAIN |
| Job remoto IPP | Windows REDACTED_LAN → page_log AD | `docs/phase1-validation.md` §2–3; checkpoint em 01-04-SUMMARY | ? UNCERTAIN |

## Goal Achievement

### Observable Truths

| # | Verdade (must-have) | Status | Evidência |
|---|---------------------|--------|-----------|
| 1 | `docker compose up` inicia CUPS sem erro em Ubuntu 22.04 (ROADMAP SC1, DEPLOY-01) | ✓ VERIFIED | `docker-compose.yml`, `cups/Dockerfile`, `scripts/bootstrap-vm.sh`; terminal ativo mostra sessão `admin-user@printwatch` executando `docker compose exec cups` |
| 2 | CUPS responde na porta 631 com ACL REDACTED_IP/16 (ROADMAP SC2, SERVER-01) | ⚠️ PARCIAL | Config: `PageLogFormat` + `Allow from ${ALLOWED_NETWORK}` em template/entrypoint; `scripts/verify-vm-network.sh` valida localhost. **Acesso remoto LAN não reproduzido pelo verificador** |
| 3 | Impressora de teste cadastrada via URI IPP (ROADMAP SC3, SERVER-03) | ✓ VERIFIED | `scripts/setup-printer.sh` (lpadmin idempotente, drivers HP/Samsung/cups-pdf); terminal VM: `lpadmin -p test_printer -v ipp://PRINTER_HOST:631/ipp/print` |
| 4 | Job de teste via IPP gera linha no page_log no formato esperado (ROADMAP SC4, SERVER-02) | ? UNCERTAIN | `PAGE_LOG_REGEX` + asserts em `validate-phase1.sh`; procedimento remoto em `docs/phase1-validation.md`. **Sem dump de page_log no repo; SUMMARY 01-04 não é evidência auditável** |
| 5 | `.env.example` contém todas as variáveis necessárias (ROADMAP SC5, DEPLOY-02) | ✓ VERIFIED | 6 chaves: `ALLOWED_NETWORK`, `CUPS_ADMIN_*`, `TEST_PRINTER_*`; validadas por `check_env_example_keys` |
| 6 | Job local via `lp` no container gera page_log válido (Plano 04) | ? UNCERTAIN | Lógica em `validate-phase1.sh` `run_full()`; não executada pelo verificador (WSL/bash indisponível; SSH batch negado) |
| 7 | Suite `validate-phase1.sh` full (sem `--quick`) passa (Plano 04) | ? UNCERTAIN | Script completo existe; execução na VM não confirmada independentemente |
| 8 | Documentação VM IP VM_HOST + hostname printwatch (Plano 03) | ✓ VERIFIED | `docs/vm-setup.md`, `docs/vm-deploy-runbook.md` |
| 9 | Bootstrap VM idempotente wired end-to-end (Plano 05) | ✓ VERIFIED | `bootstrap-vm.sh` → compose up → wait CUPS → `setup-printer.sh` → `validate-phase1.sh --quick` |
| 10 | Job remoto IPP Windows → page_log (D-13.2, Plano 04) | ? UNCERTAIN | Checkpoint documentado em 01-04-SUMMARY; requer confirmação humana |

**Score:** 7/10 verdades verificadas (3 UNCERTAIN excluídas do numerador)

### Required Artifacts

| Artefato | Esperado | Status | Detalhes |
|----------|----------|--------|----------|
| `docker-compose.yml` | Só serviço CUPS + volumes | ✓ VERIFIED | 1 serviço ativo `cups`; comentários Fase 2+ sem stubs |
| `.env.example` | Variáveis Fase 1 documentadas | ✓ VERIFIED | 6 chaves + comentários PT-BR |
| `cups/Dockerfile` | Imagem Ubuntu 22.04 + CUPS | ✓ VERIFIED | FROM ubuntu:22.04; drivers HP/Samsung/cups-pdf |
| `cups/cupsd.conf.template` | PageLogFormat + ACL | ✓ VERIFIED | Formato SPEC §3.1; não vazio |
| `cups/cups-files.conf` | Destino page_log | ✓ VERIFIED | `PageLog /var/log/cups/page_log` |
| `cups/entrypoint.sh` | envsubst + cupsd -t | ✓ VERIFIED | Whitelist `${ALLOWED_NETWORK}`; wired como ENTRYPOINT |
| `scripts/validate-phase1.sh` | Smoke + full E2E | ✓ VERIFIED | PAGE_LOG_REGEX, job lp, asserts D-14 |
| `scripts/setup-printer.sh` | lpadmin idempotente | ✓ VERIFIED | Wired via `docker compose exec` |
| `scripts/bootstrap-vm.sh` | Deploy VM automatizado | ✓ VERIFIED | Guard changeme; chama setup + validate |
| `scripts/verify-vm-network.sh` | Checks rede 631 | ✓ VERIFIED | Container, HTTP local, ACL, ufw warn |
| `docs/phase1-validation.md` | Procedimento E2E D-13/D-14 | ✓ VERIFIED | URL VM_HOST:631; DOMINIO\\usuario |
| `docs/vm-setup.md` | Checklist VM manual | ✓ VERIFIED | IP VM_HOST; link phase1-validation |
| `docs/vm-deploy-runbook.md` | Runbook deploy | ✓ VERIFIED | Sequência bootstrap + gate |

### Key Link Verification

| From | To | Via | Status | Detalhes |
|------|-----|-----|--------|----------|
| `docker-compose.yml` | `cups/` | `build: ./cups` | ✓ WIRED | Linha 6 |
| `docker-compose.yml` | `.env` | `env_file: .env` | ✓ WIRED | Linha 9 |
| `cups/entrypoint.sh` | `cupsd.conf.template` | `envsubst '${ALLOWED_NETWORK}'` | ✓ WIRED | Linhas 15–17 |
| `scripts/setup-printer.sh` | container cups | `docker compose exec … lpadmin` | ✓ WIRED | Linha 71 |
| `scripts/bootstrap-vm.sh` | `setup-printer.sh` | exec após compose up | ✓ WIRED | `run_setup_printer()` |
| `scripts/validate-phase1.sh` | `/var/log/cups/page_log` | `docker compose exec … tail/grep` | ✓ WIRED | `validate_local_job_page_log()` |
| `docs/phase1-validation.md` | endpoint IPP | `VM_HOST:631/printers/` | ✓ WIRED | Seções 2–4 |
| `docs/vm-deploy-runbook.md` | `phase1-validation.md` | link gate | ✓ WIRED | Passo 6–7 |

### Data-Flow Trace (Level 4)

Artefatos dinâmicos de runtime (page_log) — trace upstream:

| Artefato | Variável | Fonte | Produz dados reais | Status |
|----------|----------|-------|---------------------|--------|
| `validate-phase1.sh` | `last_line` (page_log) | `docker compose exec cups tail -1 /var/log/cups/page_log` | Depende de job lp real no container | ? SKIP — runtime não executado |
| `cups/entrypoint.sh` | `cupsd.conf` gerado | envsubst de template + ALLOWED_NETWORK do `.env` | Sim, quando container sobe | ✓ FLOWING (config) |

### Behavioral Spot-Checks

| Comportamento | Comando | Resultado | Status |
|---------------|---------|-----------|--------|
| Smoke Wave 0 estático | `bash scripts/validate-phase1.sh --quick` | WSL/bash indisponível no host Windows | ? SKIP |
| Smoke na VM | SSH `bash scripts/validate-phase1.sh --quick` | `Permission denied (publickey,password)` em BatchMode | ? SKIP |
| Compose config válido | `docker compose config` | Docker não testado no host verificador | ? SKIP |

**Step 7b:** SKIPPED — ambiente do verificador sem bash/WSL funcional e SSH não-interativo sem chave; runtime deve ser confirmado na VM pelo operador.

### Probe Execution

Nenhum probe `scripts/*/tests/probe-*.sh` declarado ou convencional encontrado para esta fase.

| Probe | Comando | Resultado | Status |
|-------|---------|-----------|--------|
| — | — | — | N/A |

### Requirements Coverage

| Requirement | Plano | Descrição | Status | Evidência |
|-------------|-------|-----------|--------|-----------|
| SERVER-01 | 02, 03, 04, 05 | CUPS IPP :631, rede REDACTED_IP/16 | ⚠️ PARCIAL | ACL no template; acesso LAN remoto não verificado |
| SERVER-02 | 02, 04 | PageLogFormat explícito | ✓ SATISFIED | `cupsd.conf.template` linha 4; `cups-files.conf` PageLog path |
| SERVER-03 | 03, 04, 05 | HP/Samsung IPP/socket | ✓ SATISFIED | Drivers no Dockerfile; `setup-printer.sh`; VM com `ipp://PRINTER_HOST:631/ipp/print` |
| DEPLOY-01 | 01, 02, 05 | `docker compose up -d` Ubuntu 22.04 | ⚠️ PARCIAL | Artefatos completos; execução na VM inferida (terminal), não re-auditada |
| DEPLOY-02 | 01, 03 | `.env.example` documentado | ✓ SATISFIED | 6 variáveis + comentários; gate em validate-phase1.sh |

**Requisitos órfãos:** Nenhum — todos os REQ-IDs da Fase 1 aparecem em pelo menos um plano.

### Anti-Patterns Found

| Arquivo | Linha | Padrão | Severidade | Impacto |
|---------|-------|--------|------------|---------|
| — | — | Nenhum TBD/FIXME/XXX em arquivos da fase | — | — |
| `docs/vm-setup.md` | 56 | "placeholder" (gateway DNS) | ℹ️ Info | Documentação intencional, não stub de código |

Nenhum marcador de dívida não referenciado encontrado nos arquivos modificados pela fase.

### Human Verification Required

### 1. Suite full validate-phase1 na VM

**Test:** SSH em `VM_HOST`, no diretório do repo: `bash scripts/validate-phase1.sh` (sem `--quick`).

**Expected:** Exit 0; job local `lp` gera linha no `page_log` passando `PAGE_LOG_REGEX`; printer e username validados.

**Why human:** Verificador não executou bash na VM; SUMMARY não substitui execução independente.

### 2. Job remoto IPP Windows → page_log

**Test:** Imprimir do Windows via `http://VM_HOST:631/printers/test_printer`; inspecionar `docker compose exec cups tail -1 /var/log/cups/page_log`.

**Expected:** Linha nova com `test_printer`, username AD (`DOMINIO\usuario`), timestamp recente; impressão física na impressora.

**Why human:** Critério central da fase (goal ROADMAP); evidência de checkpoint existe só em SUMMARY, não versionada.

### 3. Acesso CUPS na LAN REDACTED_LAN

**Test:** De host remoto na rede: `curl -I http://VM_HOST:631/`.

**Expected:** HTTP 200.

**Why human:** ACL verificada no config gerado; bind/publicação remota não testada pelo verificador.

### 4. URI backend impressora com porta :631

**Test:** Confirmar `.env` na VM com `TEST_PRINTER_URI=ipp://<IP>:631/ipp/print`; `./scripts/setup-printer.sh`; reimprimir do Windows.

**Expected:** Impressão física (não só entrada no page_log).

**Why human:** Terminal mostra correção em curso (socket falhou; IPP :631 aplicado); estado final não auditável no git.

### Gaps Summary

A **implementação no repositório está completa e bem conectada**: compose mínimo, container CUPS hardened, scripts de bootstrap/cadastro/validação e documentação operacional cobrem SERVER-01–03, DEPLOY-01–02 em nível de artefato.

O **objetivo da fase não está totalmente fechado** porque os comportamentos runtime críticos — job local full suite, job remoto IPP Windows e acesso LAN à porta 631 — **não foram reproduzidos pelo verificador**. O SUMMARY 01-04 afirma checkpoint aprovado com `DOMAIN\user.example` no page_log, mas isso não constitui evidência no codebase (`.env` e logs ficam na VM).

**Recomendação:** Executar os 4 itens de verificação humana acima. Se todos passarem, re-executar verificação com status `passed`.

---

_Verificado: 2026-05-26T20:00:00Z_  
_Verifier: Claude (gsd-verifier)_
