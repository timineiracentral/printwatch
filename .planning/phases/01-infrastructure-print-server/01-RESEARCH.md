# Phase 1: Infrastructure & Print Server - Research

**Researched:** 2026-05-26  
**Domain:** CUPS 2.4 + Docker Compose + Ubuntu 22.04 (print server intermediário)  
**Confidence:** HIGH (stack CUPS/Docker) / MEDIUM (username AD via IPP Windows)

## Summary

A Fase 1 é greenfield: o repositório ainda não contém código — apenas PRD, SPEC e artefatos GSD. O objetivo é validar a cadeia **Docker Compose → CUPS → impressora → `page_log`** na VM `VM_HOST`, com ACL de rede restrita a `REDACTED_IP/16`.

**Não existe imagem Docker oficial do OpenPrinting/CUPS para produção.** [CITED: github.com/OpenPrinting/cups/blob/master/docker-compose.yaml] O repositório upstream inclui um `docker-compose.yaml` de desenvolvimento (build local, usuário hardcoded), não uma imagem publicada. A abordagem correta para PrintWatch é **Dockerfile customizado baseado em Ubuntu 22.04** (alinhado a D-16/DEPLOY-01), usando pacotes `apt` do Jammy — CUPS **2.4.1op1-1ubuntu4.16** [CITED: packages.ubuntu.com/jammy/cups]. A imagem comunitária `olbat/cupsd` serve apenas como **referência de pacotes de drivers**, não como base de deploy (Debian testing, credenciais default `print/print`, ACL `Allow all`).

Descoberta crítica para SERVER-02: o default de `PageLogFormat` é **string vazia**, o que **desabilita** page logging. [CITED: cups.org/doc/man-cupsd.conf.html] [VERIFIED: Context7 /openprinting/cups] O olbat/cupsd.conf de referência comete exatamente esse erro (`PageLogFormat` sem valor). PrintWatch **deve** definir explicitamente o format da SPEC §3.1 e garantir `PageLog /var/log/cups/page_log` em `cups-files.conf`. [CITED: cups.org/doc/man-cups-files.conf.html]

**Primary recommendation:** Dockerfile Ubuntu 22.04 + entrypoint com `envsubst` para ACL + `PageLogFormat` explícito + volumes `cups_logs`/`cups_spool` + script idempotente `lpadmin` separado + suite de comandos de validação documentada.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Print server (IPP :631) | Container CUPS | VM Ubuntu (Docker host) | CUPS recebe jobs e encaminha à impressora física |
| ACL de rede CUPS | Container (`cupsd.conf`) | Firewall Fortigate/VM | Deny-by-default no CUPS; firewall externo é camada adicional, não substituto |
| Page logging (`page_log`) | Container CUPS (`cups-files.conf` + `PageLogFormat`) | Volume Docker `cups_logs` | CUPS grava log; volume persiste para Fase 2 |
| Cadastro de impressora | Script shell (host ou `docker exec`) | CUPS `lpadmin` | Operação administrativa versionada no repo (D-10) |
| Credenciais admin CUPS | Entrypoint container | `.env` (não versionado) | Usuário Linux em `@SYSTEM`/`lpadmin`; senha via env |
| IP/hostname VM | VM (netplan + hostnamectl) | — | Pré-requisito de rede antes do compose |
| Validação job remoto IPP | Cliente Windows na rede REDACTED_LAN | CUPS container | Teste end-to-end de SERVER-01 |

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Escopo do Docker Compose (Fase 1)
- **D-01:** Subir **somente** o container/serviço CUPS via `docker compose up -d`.
- **D-02:** Backend, frontend e nginx **não entram** nesta fase — nem como stub ou serviço vazio.
- **D-03:** `docker-compose.yml` deve ser escrito já pensando em expansão futura (comentários ou estrutura clara), mas **sem** serviços placeholder ativos.
- **D-04:** Objetivo exclusivo: validar cadeia de impressão e logging (`page_log`).

#### Restrição de rede do CUPS
- **D-05:** Restringir acesso CUPS **apenas** à rede `REDACTED_IP/16`.
- **D-06:** **Não** usar ranges amplos (192.168/10/172 genéricos da SPEC) nesta fase.
- **D-07:** Adotar postura **deny-by-default** no `cupsd.conf` — permitir explicitamente só `REDACTED_IP/16`.
- **D-08:** `ALLOWED_NETWORK=REDACTED_IP/16` deve existir no `.env.example` desde a Fase 1 e ser consumido pela configuração do CUPS.

#### Cadastro da impressora de teste
- **D-09:** Sem UI web nesta fase (SERVER-04 é Fase 5).
- **D-10:** Cadastro via **script shell versionado** no repositório + **documentação** do passo manual equivalente.
- **D-11:** Script deve usar `lpadmin` de forma **idempotente** (reexecutável sem duplicar impressora).
- **D-12:** Impressoras de teste: HP ou Samsung por **IPP ou socket**, conforme disponibilidade do equipamento.

#### Validação do job de teste
- **D-13:** Validar em **dois modos**:
  1. Job local via `lp` **dentro do container** (sanidade rápida)
  2. Job remoto via **IPP** de uma máquina na rede `REDACTED_IP/16`
- **D-14:** Critérios de aceite do `page_log`:
  - Linha presente no `page_log` após cada job
  - `username` no formato `DOMINIO\usuario`
  - Nome da impressora correto
  - Timestamp correto
- **D-15:** `PageLogFormat` deve ser configurado explicitamente no `cupsd.conf` (SERVER-02) conforme SPEC.md §3.1 — adaptando ACL de rede para `REDACTED_IP/16`.

#### Preparação da VM e variáveis de ambiente
- **D-16:** Reutilizar VM Ubuntu 22.04 existente no XCP-ng (não provisionar nova).
- **D-17:** IP estático **obrigatório** na Fase 1: `VM_HOST`.
- **D-18:** Hostname deve ser definido na Fase 1 — usar `printwatch` (alinhado ao nome do projeto/serviço).
- **D-19:** Credenciais admin do CUPS **não versionadas** — apenas placeholders no `.env.example` (`CUPS_ADMIN_USER`, `CUPS_ADMIN_PASSWORD`).
- **D-20:** `.env.example` documenta todas as variáveis necessárias para esta fase (DEPLOY-02).

#### Princípios operacionais (Fase 1)
- **D-21:** Priorizar **simplicidade operacional** — chegar rápido ao `page_log` válido.
- **D-22:** Sem observabilidade/dashboard, integração AD, otimização HA/redundância nesta fase.

### Claude's Discretion
- Formato exato do hostname DNS interno (FQDN vs short name) — default `printwatch`, ajustável no plano se o AD exigir sufixo.
- Nome do arquivo/script de setup da impressora e localização no repo (`scripts/` vs `cups/`).
- Detalhes do Dockerfile/entrypoint do CUPS desde que respeitem D-01 a D-20.
- Driver/protocolo IPP vs socket para impressora específica de teste — escolher o que funcionar com o hardware disponível.

### Deferred Ideas (OUT OF SCOPE)
- **ROADMAP GSD parsing** — Migrar headings de `## Fase N:` para `### Phase N:` em `.planning/ROADMAP.md` para compatibilidade com `gsd-tools` (solicitado pelo usuário para correção posterior).
- **UI de cadastro de impressoras** — SERVER-04, Fase 5.
- **Backend/frontend/nginx no compose** — Fases 2–4; não stub na Fase 1.
- **Integração AD/LDAP** — Fase 2+.
- **Observabilidade e dashboard** — Fases 3–4.
- **HA/redundância** — fora do MVP.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SERVER-01 | CUPS na porta 631 acessível via IPP pela faixa REDACTED_IP/16 | `Listen *:631` + ACL deny-by-default com `Allow from ${ALLOWED_NETWORK}` em `<Location />`, `<Location /admin>`, etc.; validação via `curl`/`ippfind` |
| SERVER-02 | `PageLogFormat` configurado explicitamente para formato do parser | Default vazio desabilita logging — definir string SPEC §3.1; `PageLog` em `cups-files.conf`; volume persistente |
| SERVER-03 | Suporte HP/Samsung por IP (IPP ou socket) | `-m everywhere` para IPP Everywhere; `socket://IP:9100` + PPD PostScript como fallback; pacotes `hp-ppd`, `printer-driver-splix`, `cups-filters` |
| DEPLOY-01 | Deploy reproduzível via `docker compose up -d` em Ubuntu 22.04 | Dockerfile `ubuntu:22.04` + apt CUPS 2.4.1; compose só serviço `cups`; prereq Docker na VM |
| DEPLOY-02 | `.env.example` documentado | Variáveis Fase 1: `ALLOWED_NETWORK`, `CUPS_ADMIN_USER`, `CUPS_ADMIN_PASSWORD`, URIs da impressora de teste |

</phase_requirements>

## Standard Stack

### Core

| Componente | Versão | Purpose | Why Standard |
|-----------|---------|---------|--------------|
| Ubuntu base image | 22.04 LTS (jammy) | Base do container CUPS | Alinha VM host (D-16) e pacotes testados |
| CUPS (`cups`, `cups-client`, `cups-filters`) | 2.4.1op1-1ubuntu4.16 | Print server IPP | [CITED: packages.ubuntu.com/jammy/cups] Padrão Ubuntu 22.04 |
| Docker Compose | v2 plugin | Orquestração | DEPLOY-01; SPEC §3.5 |
| `envsubst` (gettext-base) | apt jammy | Template `cupsd.conf` | Padrão Docker para configs estáticas + env [CITED: nginx/docker pattern] |
| `lpadmin` / `lp` | cups-client | Cadastro e jobs de teste | [VERIFIED: Context7 /openprinting/cups] |

### Supporting (apt, no container npm/pip)

| Pacote | Purpose | When to Use |
|--------|---------|-------------|
| `hp-ppd` | Drivers HP | Impressora HP sem IPP Everywhere |
| `printer-driver-splix` | Drivers Samsung | Impressora Samsung via socket/PPD |
| `openprinting-ppds` | PPDs genéricos | Fallback PostScript |
| `printer-driver-cups-pdf` | Impressora virtual PDF | Teste **sem hardware** (sanidade page_log) [ASSUMED] |
| `curl`, `ippfind` | Validação | Smoke tests Nyquist |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Dockerfile custom Ubuntu 22.04 | `olbat/cupsd` | olbat usa Debian testing, ACL aberta, PageLogFormat vazio — incompatível com D-05–D-08, D-15 |
| Dockerfile custom | OpenPrinting dev compose | Apenas dev upstream; sem imagem publicada |
| IPP `-m everywhere` | socket + PPD | IPP preferido (driverless); socket fallback para equipamentos legados |
| `envsubst` template | Montar cupsd.conf estático | Estático quebra D-08 (ALLOWED_NETWORK parametrizável) |

**Installation (VM host):**
```bash
# Pré-requisitos na VM Ubuntu 22.04
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER
```

**Build/deploy:**
```bash
cp .env.example .env   # editar credenciais e URI da impressora
docker compose up -d --build
./scripts/setup-printer.sh   # após CUPS healthy
```

## Package Legitimacy Audit

> Fase 1 **não instala pacotes npm/pip**. Stack via imagem Docker + `apt`. slopcheck executado mas sem pacotes npm para auditar.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| *(nenhum npm/pip)* | — | — | — | — | N/A | N/A — fase usa apt Ubuntu |

**Pacotes apt críticos (verificados no repositório Ubuntu jammy):**

| Pacote | Versão jammy | Fonte |
|--------|--------------|-------|
| `cups` | 2.4.1op1-1ubuntu4.16 | [CITED: packages.ubuntu.com/jammy/cups] |
| `cups-client` | 2.4.1op1-1ubuntu4.16 | [CITED: packages.ubuntu.com/jammy/cups] |

**Packages removed due to slopcheck [SLOP] verdict:** none  
**Packages flagged as suspicious [SUS]:** none

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  VM Ubuntu 22.04 (VM_HOST, hostname: printwatch)          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  docker compose (Fase 1: só serviço cups)                 │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  Container: cups                                     │  │  │
│  │  │  entrypoint: envsubst → cupsd.conf                   │  │  │
│  │  │              create admin user                     │  │  │
│  │  │              cupsd -t → cupsd -f                     │  │  │
│  │  │  :631 IPP ◄──────────────────────────────────────┐  │  │  │
│  │  │       │                                           │  │  │  │
│  │  │       ▼                                           │  │  │  │
│  │  │  lpadmin queue ──► impressora física HP/Samsung  │  │  │  │
│  │  │       │                                           │  │  │  │
│  │  │       ▼                                           │  │  │  │
│  │  │  /var/log/cups/page_log ──► volume cups_logs     │  │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         ▲                              ▲
         │ IPP (REDACTED_IP/16)           │ lp local (docker exec)
         │                              │
   PC Windows                      setup-printer.sh
   (validação remota D-13)         (lpadmin idempotente)
```

### Recommended Project Structure

```
printwatch/
├── docker-compose.yml       # só cups + volumes declarados (D-01, D-03)
├── .env.example             # DEPLOY-02
├── cups/
│   ├── Dockerfile           # FROM ubuntu:22.04
│   ├── cupsd.conf.template  # ${ALLOWED_NETWORK}, PageLogFormat fixo
│   ├── cups-files.conf      # PageLog /var/log/cups/page_log
│   └── entrypoint.sh        # envsubst, admin user, cupsd -t, exec
└── scripts/
    ├── setup-printer.sh     # lpadmin idempotente (D-10, D-11)
    └── validate-phase1.sh   # smoke tests Nyquist (opcional)
```

### Pattern 1: ACL deny-by-default com template env

**What:** Gerar `cupsd.conf` em runtime a partir de template com `ALLOWED_NETWORK`.  
**When to use:** Sempre — D-07, D-08.  
**Example:**
```bash
# entrypoint.sh — padrão envsubst (nginx/docker)
# Source: [CITED: cups.org/doc/man-cupsd.conf.html] + [ASSUMED: envsubst pattern]
export ALLOWED_NETWORK="${ALLOWED_NETWORK:-REDACTED_IP/16}"
envsubst '${ALLOWED_NETWORK}' \
  < /etc/cups/cupsd.conf.template \
  > /etc/cups/cupsd.conf
/usr/sbin/cupsd -t || exit 1
exec /usr/sbin/cupsd -f
```

```apache
# cupsd.conf.template (trecho)
Listen *:631
PageLogFormat "%p %u %j %T %P %C %{job-billing} %{job-originating-host-name} %{job-name} %{media} %{sides}"

<Location />
  Order allow,deny
  Allow from ${ALLOWED_NETWORK}
</Location>

<Location /admin>
  AuthType Default
  Require user @SYSTEM
  Order allow,deny
  Allow from ${ALLOWED_NETWORK}
</Location>
```

**Nota CUPS 2.4:** `Order allow,deny` + `Allow from CIDR` permanece funcional em 2.4.16. [CITED: github.com/OpenPrinting/cups v2.4.16/conf/cupsd.conf.in] Diretivas `JobPrivateAccess` etc. **devem** ficar dentro de `<Policy>`, nunca no top-level — senão `cupsd -t` falha. [CITED: askubuntu.com/questions/1560253]

### Pattern 2: PageLogFormat + PageLog (SERVER-02)

**What:** Habilitar page logging com format compatível com parser da Fase 2.  
**When to use:** Obrigatório — default vazio desabilita logging.  
**Example:**
```apache
# cupsd.conf — NÃO deixar PageLogFormat vazio
PageLogFormat "%p %u %j %T %P %C %{job-billing} %{job-originating-host-name} %{job-name} %{media} %{sides}"
```

```apache
# cups-files.conf
# Source: [CITED: cups.org/doc/man-cups-files.conf.html]
PageLog /var/log/cups/page_log
LogFilePerm 0644
```

**Formato de linha esperado** (default CUPS, uma linha por página):
```
printer user job-id [DD/Mon/YYYY:HH:MM:SS +ZZZZ] total N billing host job-name media sides
```
[CITED: cups.org/doc/man-cupsd-logs.html]

### Pattern 3: lpadmin idempotente

**What:** Script reexecutável que cria/atualiza impressora sem duplicar.  
**When to use:** D-10, D-11, SERVER-03.  
**Example:**
```bash
#!/usr/bin/env bash
# Source: [CITED: cups.org/doc/admin.html] + [CITED: manpages.debian.org lpadmin]
set -euo pipefail

PRINTER_NAME="${TEST_PRINTER_NAME:-test_printer}"
PRINTER_URI="${TEST_PRINTER_URI:-ipp://192.168.1.100/ipp/print}"
PRINTER_DRIVER="${TEST_PRINTER_DRIVER:-everywhere}"

if lpstat -p "$PRINTER_NAME" >/dev/null 2>&1; then
  CURRENT_URI="$(lpstat -v "$PRINTER_NAME" 2>/dev/null | awk '{print $NF}')"
  if [ "$CURRENT_URI" = "$PRINTER_URI" ]; then
    echo "Printer $PRINTER_NAME already configured"
    exit 0
  fi
  lpadmin -p "$PRINTER_NAME" -v "$PRINTER_URI" -m "$PRINTER_DRIVER" -E
else
  lpadmin -p "$PRINTER_NAME" -v "$PRINTER_URI" -m "$PRINTER_DRIVER" -E
fi
cupsaccept "$PRINTER_NAME"
cupsenable "$PRINTER_NAME"
```

**URI patterns HP/Samsung:**

| Protocolo | URI exemplo | Driver |
|-----------|-------------|--------|
| IPP Everywhere | `ipp://10.x.x.x/ipp/print` | `-m everywhere` [VERIFIED: Context7] |
| IPP clássico | `ipp://10.x.x.x/ipp` | `-m everywhere` ou PPD específico |
| Socket (JetDirect) | `socket://10.x.x.x:9100` | PPD PostScript genérico |

### Pattern 4: Docker Compose Fase 1 only

**What:** Compose mínimo com volumes preparados para Fase 2.  
**When to use:** D-01, D-03, DEPLOY-01.  
**Example:**
```yaml
# docker-compose.yml — Fase 1
services:
  cups:
    build: ./cups
    ports:
      - "631:631"
    env_file: .env
    environment:
      ALLOWED_NETWORK: ${ALLOWED_NETWORK:-REDACTED_IP/16}
      CUPS_ADMIN_USER: ${CUPS_ADMIN_USER}
      CUPS_ADMIN_PASSWORD: ${CUPS_ADMIN_PASSWORD}
    volumes:
      - cups_logs:/var/log/cups
      - cups_spool:/var/spool/cups
    restart: unless-stopped

  # Fase 2+: backend (montará cups_logs:ro)
  # Fase 4+: frontend + nginx

volumes:
  cups_logs:
  cups_spool:
```

### Pattern 5: Admin CUPS via env (D-19)

**What:** Criar usuário Linux membro de `lpadmin`/`@SYSTEM` no entrypoint.  
**When to use:** Admin web :631/admin (opcional Fase 1) e operações `lpadmin`.  
**Example:**
```bash
# Source: [CITED: github.com/OpenPrinting/cups/issues/1080]
if ! id "$CUPS_ADMIN_USER" &>/dev/null; then
  useradd -r -G lpadmin,sys,root "$CUPS_ADMIN_USER"
  echo "${CUPS_ADMIN_USER}:${CUPS_ADMIN_PASSWORD}" | chpasswd
fi
```

### Anti-Patterns to Avoid

- **PageLogFormat vazio ou ausente:** logging desabilitado — causa raiz comum de `page_log` vazio [CITED: cups.org/doc/man-cupsd.conf.html]
- **Usar imagem olbat/cupsd sem hardening:** ACL `Allow all`, PageLogFormat vazio
- **Editar `printers.conf` manualmente:** lpadmin é a API suportada [CITED: manpages.debian.org lpadmin]
- **JobPrivateAccess fora de `<Policy>`:** cupsd 2.4.1+ rejeita config [CITED: askubuntu.com]
- **Stub backend/nginx “para depois”:** viola D-02

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Print server IPP | Servidor HTTP custom | CUPS | Protocolo IPP, spooling, backends |
| Page log parsing (Fase 1) | Parser próprio | Validar regex SPEC §3.2 contra linha real | Parser completo é Fase 2 |
| ACL por iptables só | Firewall como única barreira | `cupsd.conf` deny-by-default + firewall opcional | SERVER-01 exige controle no CUPS |
| Template de config | sed ad-hoc multi-linha | `envsubst` com template dedicado | Menos frágil, whitelist de vars |
| Descoberta de impressora | Script de scan custom | `lpinfo -v` + URI manual no `.env` | Simplicidade operacional (D-21) |

## Common Pitfalls

### Pitfall 1: page_log permanece vazio

**What goes wrong:** Jobs imprimem mas `/var/log/cups/page_log` não cresce.  
**Why it happens:** `PageLogFormat` default é string vazia; alguns cupsd.conf comunitários deixam `PageLogFormat` sem valor. [CITED: cups.org/doc/man-cupsd.conf.html]  
**How to avoid:** Definir `PageLogFormat` da SPEC; confirmar `PageLog` em `cups-files.conf`; reiniciar cupsd.  
**Warning signs:** `cupsd -t` OK mas arquivo vazio ou inexistente.

### Pitfall 2: cupsd -t falha após merge de configs

**What goes wrong:** Container reinicia em loop.  
**Why it happens:** Diretivas de Policy (`JobPrivateAccess`, etc.) colocadas fora de `<Policy>`. [CITED: Launchpad #2133210]  
**How to avoid:** Copiar estrutura de Policy do `cupsd.conf.in` oficial v2.4.16; rodar `cupsd -t` no entrypoint antes de `exec`.  
**Warning signs:** `Unknown directive JobPrivateAccess on line N`.

### Pitfall 3: Username AD não chega como `DOMINIO\usuario`

**What goes wrong:** `page_log` mostra username curto, vazio ou IP.  
**Why it happens:** Windows IPP nem sempre envia `requesting-user-name` no formato esperado; depende de driver/conta logada. [ASSUMED — risco documentado em PROJECT.md]  
**How to avoid:** Job local de sanidade com `lp -U 'DOMINIO\usuario'`; job remoto documentar driver IPP nativo; aceitar validação parcial na Fase 1 se hardware Windows indisponível.  
**Warning signs:** Campo `user` no page_log é `-`, `guest`, ou hostname.

### Pitfall 4: Impressora offline / driver ausente no container

**What goes wrong:** Job fica na fila; page_log pode não registrar conclusão.  
**Why it happens:** PPD/driver errado; URI incorreta; impressora não alcançável da rede do container.  
**How to avoid:** Testar conectividade `ping`/`curl ipp://`; preferir `-m everywhere`; incluir `printer-driver-cups-pdf` para teste sem hardware.  
**Warning signs:** `lpstat -t` mostra impressora disabled; `error_log` com backend errors.

### Pitfall 5: ACL bloqueia admin local mas permite rede errada

**What goes wrong:** Validação remota falha ou admin inacessível.  
**Why it happens:** `Allow from` só em `<Location />` mas não em `/admin` ou `/printers`.  
**How to avoid:** Replicar ACL em todos os blocos `<Location>` relevantes; incluir `localhost` implícito via `@LOCAL` se necessário para healthchecks internos.  
**Warning signs:** `403 Forbidden` no curl da rede REDACTED_LAN.

## Code Examples

### Validar config CUPS antes de subir

```bash
# Source: [CITED: cups.org/doc/man-cupsd.conf.html]
docker compose exec cups cupsd -t
# Esperado: saída vazia (exit 0)
```

### Job local de sanidade (D-13 modo 1)

```bash
# Source: [VERIFIED: Context7 /openprinting/cups]
docker compose exec cups bash -c \
  'echo "PrintWatch phase1 test" | lp -d '"${TEST_PRINTER_NAME}"' -U '"'"'DOMINIO\usuario'"'"' -t phase1-local-test'
sleep 2
docker compose exec cups tail -n 5 /var/log/cups/page_log
```

### Verificar IPP acessível (SERVER-01)

```bash
# De máquina na rede REDACTED_IP/16:
curl -sI "http://VM_HOST:631/" | head -1
# Esperado: HTTP/1.1 200 OK

ippfind -T 5 VM_HOST
# Esperado: impressoras anunciadas (se Browsing On)
```

### Job remoto Windows (D-13 modo 2)

```
URL: http://VM_HOST:631/printers/<nome>
Protocolo: IPP
Driver: nativo HP/Samsung ou IPP Class Driver
```

Após imprimir, na VM:
```bash
docker compose exec cups grep '<nome_impressora>' /var/log/cups/page_log | tail -1
```

### .env.example (DEPLOY-02)

```env
# Rede permitida no CUPS (D-08)
ALLOWED_NETWORK=REDACTED_IP/16

# Admin CUPS — NÃO commitar valores reais (D-19)
CUPS_ADMIN_USER=admin
CUPS_ADMIN_PASSWORD=changeme

# Impressora de teste (setup-printer.sh)
TEST_PRINTER_NAME=test_printer
TEST_PRINTER_URI=ipp://192.0.2.50/ipp/print
TEST_PRINTER_DRIVER=everywhere
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| CUPS 1.x em bare-metal | CUPS 2.4.x em container | Ubuntu 22.04+ | Validar `cupsd -t` rigoroso |
| `Allow from` ranges RFC1918 amplos | Só `REDACTED_IP/16` | PrintWatch D-06 | Adaptar SPEC §3.1 |
| PageLog default implícito | PageLogFormat explícito | Sempre foi necessário | Default vazio = sem log |
| PPD obrigatório | IPP Everywhere (`-m everywhere`) | CUPS 2.x+ | Simplifica HP/Samsung modernos |

**Deprecated/outdated:**
- Confiar em PageLogFormat default do CUPS — desabilita logging [CITED: cups.org]
- Imagem `olbat/cupsd` como drop-in — ACL e logging incompatíveis com PrintWatch

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Windows envia `DOMINIO\usuario` via IPP com driver moderno | Pitfall 3 | page_log com username incorreto; mitigação na Fase 2 |
| A2 | `printer-driver-cups-pdf` aceitável para teste sem hardware | Standard Stack | Pode não exercitar backend IPP real |
| A3 | FQDN `printwatch` suficiente (sem sufixo AD) | User Constraints | Ajustar hostname se AD exigir |
| A4 | Container bridge Docker alcança impressoras na LAN REDACTED_LAN | Architecture | Pode precisar `network_mode: host` — validar na VM |
| A5 | `@SYSTEM` inclui usuário criado em `lpadmin` | Pattern 5 | Admin web pode falhar autenticação |

## Open Questions

1. **Impressora física disponível para teste?**
   - What we know: HP ou Samsung por IP (D-12)
   - What's unclear: IP/URI exato e suporte IPP Everywhere
   - Recommendation: parametrizar no `.env`; fallback `cups-pdf` para CI/sanidade local

2. **Docker bridge vs host network para alcançar impressoras?**
   - What we know: Impressoras na mesma LAN REDACTED_LAN
   - What's unclear: Routing XCP-ng → container → impressora
   - Recommendation: default bridge; escalar para `network_mode: host` só se `lpadmin`/job falhar por rota

3. **Formato exato do username no job Windows real**
   - What we know: D-14 exige `DOMINIO\usuario`; PROJECT.md marca risco alto
   - What's unclear: Comportamento com IPP Class Driver vs driver vendor
   - Recommendation: documentar resultado observado; normalização fica Fase 2

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Docker | DEPLOY-01 | ✓ (dev machine) | 28.3.0 | Instalar na VM: `apt install docker.io` |
| Docker Compose v2 | DEPLOY-01 | ✓ (dev machine) | v2.38.1 | Plugin `docker-compose-plugin` na VM |
| Ubuntu 22.04 VM | D-16 | ✗ (não verificada nesta sessão) | — | Reutilizar VM XCP-ng existente |
| Impressora HP/Samsung IP | SERVER-03 | ? | — | `printer-driver-cups-pdf` para sanidade |
| PC Windows REDACTED_LAN | D-13 remoto | ? | — | Adiar validação remota; bloquear UAT parcial |
| Node/Python tests | Nyquist | ✓ local | node 22 / py 3.13 | Fase 1 usa shell smoke tests, não pytest |

**Missing dependencies with no fallback:**
- VM `VM_HOST` configurada (pré-requisito operacional)

**Missing dependencies with fallback:**
- Impressora física → impressora PDF CUPS
- PC Windows → validar só job local na Fase 1 (UAT parcial documentado)

## Validation Architecture

> Nyquist habilitado (`workflow.nyquist_validation: true`). Projeto greenfield — sem framework de testes ainda. Fase 1 usa **smoke tests shell** (< 30s cada).

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Bash smoke tests (sem pytest/jest ainda) |
| Config file | `scripts/validate-phase1.sh` (a criar no Wave 0) |
| Quick run command | `bash scripts/validate-phase1.sh --quick` |
| Full suite command | `bash scripts/validate-phase1.sh` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DEPLOY-01 | Compose sobe sem erro | smoke | `docker compose up -d --build && docker compose ps --format json \| grep -i running` | ❌ Wave 0 |
| DEPLOY-01 | Config CUPS válida | smoke | `docker compose exec -T cups cupsd -t` | ❌ Wave 0 |
| SERVER-01 | CUPS responde :631 | smoke | `curl -sf -o /dev/null -w '%{http_code}' http://127.0.0.1:631/` → `200` | ❌ Wave 0 |
| SERVER-01 | ACL rede (manual parcial) | manual | curl de IP REDACTED_LAN vs IP externo | ❌ |
| SERVER-02 | PageLogFormat ativo | smoke | `docker compose exec -T cups grep PageLogFormat /etc/cups/cupsd.conf \| grep -v '""'` | ❌ Wave 0 |
| SERVER-02 | page_log recebe linha | integration | job local `lp` + `grep` no page_log | ❌ Wave 0 |
| SERVER-03 | Impressora cadastrada | smoke | `docker compose exec -T cups lpstat -p $TEST_PRINTER_NAME` | ❌ Wave 0 |
| DEPLOY-02 | .env.example completo | unit | `grep -E 'ALLOWED_NETWORK\|CUPS_ADMIN' .env.example` | ❌ Wave 0 |

### Regex de validação page_log (alinhado SPEC §3.2)

```bash
# Esperado após job de teste:
PAGE_LOG_REGEX='^(\S+)\s+(\S+)\s+(\d+)\s+\[(.+?)\]\s+total\s+(\d+)\s+(\S+)\s+(\S+)\s+(.+?)\s+(\S+)\s+(\S+)$'
grep -E "$PAGE_LOG_REGEX" /var/log/cups/page_log
```

### Sampling Rate

- **Per task commit:** `docker compose exec -T cups cupsd -t`
- **Per wave merge:** `bash scripts/validate-phase1.sh --quick`
- **Phase gate:** job local + (idealmente) job remoto IPP + page_log válido

### Wave 0 Gaps

- [ ] `scripts/validate-phase1.sh` — smoke tests automatizados
- [ ] `scripts/setup-printer.sh` — lpadmin idempotente
- [ ] `cups/Dockerfile` + `entrypoint.sh` + templates
- [ ] `docker-compose.yml` + `.env.example`
- [ ] Documentação VM prep (`docs/vm-setup.md` ou seção README)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes (admin CUPS) | Basic auth via usuário `@SYSTEM`; senha em `.env` |
| V3 Session Management | no | N/A Fase 1 |
| V4 Access Control | yes | `Order allow,deny` + `Allow from REDACTED_IP/16` |
| V5 Input Validation | yes | Validar CIDR em `ALLOWED_NETWORK`; `cupsd -t` |
| V6 Cryptography | no | Sem TLS obrigatório no MVP LAN |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| CUPS exposto além da LAN | Spoofing/Tampering | ACL deny-by-default; sem port forward externo |
| Credenciais admin default | Elevation | D-19: placeholders only; senha forte em `.env` |
| Config injection via env | Tampering | `envsubst` whitelist só `${ALLOWED_NETWORK}` |
| Log file world-readable | Information Disclosure | `LogFilePerm 0644`; volume não exposto à rede |

## VM Prep Checklist (D-16–D-18)

| Step | Command / Ação | Verificação |
|------|----------------|-------------|
| Hostname | `sudo hostnamectl set-hostname printwatch` | `hostname` → `printwatch` |
| IP estático | Netplan: `VM_HOST/16` (ajustar gateway/DNS) | `ip addr show` |
| Docker | `apt install docker.io docker-compose-plugin` | `docker compose version` |
| Clone repo | `git clone ... && cd printwatch` | — |
| Deploy | `cp .env.example .env && docker compose up -d --build` | `docker compose ps` |
| Impressora | `./scripts/setup-printer.sh` | `lpstat -p` |
| Validação | `./scripts/validate-phase1.sh` | exit 0 |

**Netplan exemplo** [ASSUMED — ajustar gateway real]:
```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses: [VM_HOST/16]
      gateway4: NETWORK_GATEWAY
      nameservers:
        addresses: [NETWORK_GATEWAY]
```

## Project Constraints (from .cursor/rules/)

- Edições de código devem entrar via workflow GSD (`/gsd-execute-phase`, `/gsd-quick`, etc.) — não editar fora do fluxo salvo pedido explícito.
- Stack ainda não documentada em `.cursor/rules/` — seguir SPEC.md e CONTEXT.md como fonte canônica.
- Sem project skills locais — aplicar convenções emergentes do SPEC.

## Sources

### Primary (HIGH confidence)
- [VERIFIED: Context7 /openprinting/cups] — lpadmin, IPP everywhere, PageLogFormat default, PageLog path
- [CITED: cups.org/doc/man-cupsd.conf.html] — PageLogFormat, Allow/Deny/Order ACL
- [CITED: cups.org/doc/man-cups-files.conf.html] — PageLog directive
- [CITED: cups.org/doc/man-cupsd-logs.html] — formato page_log
- [CITED: packages.ubuntu.com/jammy/cups] — versão CUPS 2.4.1op1 Ubuntu 22.04

### Secondary (MEDIUM confidence)
- [CITED: github.com/olbat/dockerfiles/tree/master/cupsd] — lista pacotes drivers (referência, não deploy)
- [CITED: github.com/OpenPrinting/cups v2.4.16/conf/cupsd.conf.in] — estrutura Policy/Location
- [CITED: github.com/OpenPrinting/cups/issues/1080] — padrão admin user via env
- [CITED: askubuntu.com/questions/1560253] — cupsd -t JobPrivateAccess pitfall

### Tertiary (LOW confidence — validar na VM)
- [ASSUMED] Comportamento username Windows IPP → CUPS page_log
- [ASSUMED] Docker bridge alcança impressoras LAN sem `network_mode: host`

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — CUPS/Ubuntu/Docker documentados oficialmente
- Architecture: **HIGH** — SPEC + CONTEXT locked; padrões envsubst/lpadmin verificados
- Pitfalls: **MEDIUM** — username AD e networking container→impressora precisam validação na VM

**Research date:** 2026-05-26  
**Valid until:** 2026-06-26 (CUPS 2.4.x estável; revisar se Ubuntu cups security update alterar cupsd.conf schema)

## RESEARCH COMPLETE

**Phase:** 1 - Infrastructure & Print Server  
**Confidence:** HIGH (infra CUPS/Docker) / MEDIUM (integração Windows/AD)

### Key Findings
- Não há imagem Docker oficial CUPS — usar Dockerfile custom Ubuntu 22.04
- `PageLogFormat` vazio **desabilita** page_log; olbat/cupsd comete esse erro
- ACL deny-by-default: `Order allow,deny` + `Allow from REDACTED_IP/16` via `envsubst`
- lpadmin idempotente: checar `lpstat -p` antes de criar; preferir `-m everywhere` para IPP
- Username `DOMINIO\usuario` no page_log remoto é risco alto — validar com job Windows real

### File Created
`.planning/phases/01-infrastructure-print-server/01-RESEARCH.md`

### Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| Standard Stack | HIGH | Docs CUPS + Ubuntu packages verificados |
| Architecture | HIGH | Decisions D-01–D-22 + SPEC mapeados |
| Pitfalls | MEDIUM | AD username e rede container→printer não testados na VM |

### Open Questions
- URI/driver da impressora física de teste
- Docker bridge vs host network na VM XCP-ng
- Formato real do username enviado por Windows IPP

### Ready for Planning
Research complete. Planner can now create PLAN.md files.
