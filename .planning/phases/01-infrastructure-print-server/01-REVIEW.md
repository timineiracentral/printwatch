---
phase: 01-infrastructure-print-server
reviewed: 2026-05-26T12:00:00Z
depth: standard
files_reviewed: 12
files_reviewed_list:
  - docker-compose.yml
  - cups/Dockerfile
  - cups/entrypoint.sh
  - cups/cupsd.conf.template
  - cups/cups-files.conf
  - scripts/bootstrap-vm.sh
  - scripts/setup-printer.sh
  - scripts/validate-phase1.sh
  - scripts/verify-vm-network.sh
  - docs/vm-setup.md
  - docs/vm-deploy-runbook.md
  - docs/phase1-validation.md
findings:
  critical: 3
  warning: 6
  info: 2
  total: 11
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-05-26T12:00:00Z  
**Depth:** standard  
**Files Reviewed:** 12  
**Status:** issues_found

## Summary

Revisão adversarial da infraestrutura CUPS da Fase 1 (Compose, container, scripts de deploy/validação e documentação operacional). A cadeia básica Docker → CUPS → `page_log` está bem estruturada e inclui mitigações conscientes (`envsubst` whitelist, validação CIDR básica, `cupsd -t` no entrypoint, bootstrap que rejeita `changeme`).

Foram encontrados **3 problemas críticos** relacionados a credenciais fracas por padrão, injeção de comando via variáveis `.env` interpoladas em shell, e impressão anônima em toda a rede `/16`. Há também lacunas operacionais (senha admin não rotacionada em restart, ACL hardcoded nos testes) e hardening incompleto (bind `0.0.0.0`, usuário admin no grupo `root`).

## Critical Issues

### CR-01: Container sobe com senha padrão `changeme` sem falhar

**File:** `cups/entrypoint.sh:6-7`  
**Issue:** Se `CUPS_ADMIN_PASSWORD` não estiver definido (ou `docker compose up` for executado sem passar pelo `bootstrap-vm.sh`), o entrypoint usa fallback `changeme`. O serviço inicia normalmente — apenas o bootstrap bloqueia essa senha, não o container em si. Em produção, um deploy direto via Compose expõe credenciais admin CUPS conhecidas em toda a rede `REDACTED_IP/16` (interface web `/admin` exige auth, mas a senha é trivial).

**Fix:**
```bash
CUPS_ADMIN_PASSWORD="${CUPS_ADMIN_PASSWORD:-}"

if [[ -z "${CUPS_ADMIN_PASSWORD}" || "${CUPS_ADMIN_PASSWORD}" == "changeme" ]]; then
  echo "CUPS_ADMIN_PASSWORD ausente ou igual a 'changeme' — defina no .env antes de subir" >&2
  exit 1
fi
```

### CR-02: Injeção de comando via variáveis `TEST_PRINTER_*` no host

**File:** `scripts/setup-printer.sh:71-75`  
**Issue:** `run_lpadmin_idempotent` monta `docker compose exec … bash -c "…"` com **aspas duplas** no host. Valores de `PRINTER_NAME`, `PRINTER_URI` ou `PRINTER_DRIVER` vindos do `.env` são expandidos pelo shell do host antes do `exec`. Um URI malicioso como `ipp://x$(id)/` ou `foo'; whoami; echo '` executa comandos no host do operador. Mesmo com `.env` “confiável”, é um vetor real em copy-paste errado ou `.env` editado por terceiro.

**Fix:** Passar variáveis sem interpolação no host — por exemplo via `-e` ou heredoc:
```bash
docker compose exec -T \
  -e "PRINTER_NAME=${PRINTER_NAME}" \
  -e "PRINTER_URI=${PRINTER_URI}" \
  -e "PRINTER_DRIVER=${PRINTER_DRIVER}" \
  cups bash -s <<'INNER'
set -euo pipefail
# usar "$PRINTER_NAME" etc. — sem expansão no host
INNER
```

### CR-03: Policy `default` permite impressão sem autenticação em toda a rede `/16`

**File:** `cups/cupsd.conf.template:56-58`  
**Issue:** O bloco `<Limit Create-Job Print-Job Print-URI Validate-Job>` na policy `default` usa `Order deny,allow` **sem** `AuthType` nem `Require user`. Qualquer host em `REDACTED_IP/16` (via ACL `<Location />`) pode enviar jobs de impressão sem credenciais. Para um print server de monitoramento, isso permite abuso de quota/papel e jobs sem rastreabilidade de usuário AD — contradiz parcialmente D-14 (username `DOMINIO\usuario`).

**Fix:** Exigir autenticação na policy default (espelhando `authenticated`) ou restringir Create-Job/Print-Job com `AuthType Default` + `Require user @SYSTEM` / `@OWNER` conforme modelo de auth desejado para Fase 2:
```apache
<Limit Create-Job Print-Job Print-URI Validate-Job>
  AuthType Default
  Order deny,allow
</Limit>
```

## Warnings

### WR-01: Senha admin CUPS não é atualizada em restart do container

**File:** `cups/entrypoint.sh:20-23`  
**Issue:** `useradd` + `chpasswd` só rodam quando o usuário **não existe**. Em `docker compose restart` (mesmo container, filesystem preservado), alterar `CUPS_ADMIN_PASSWORD` no `.env` não aplica a nova senha — operador acredita ter rotacionado credencial, mas a antiga permanece ativa.

**Fix:** Sempre sincronizar senha após garantir que o usuário existe:
```bash
if ! id "${CUPS_ADMIN_USER}" &>/dev/null; then
  useradd -r -G lpadmin,sys "${CUPS_ADMIN_USER}"
fi
echo "${CUPS_ADMIN_USER}:${CUPS_ADMIN_PASSWORD}" | chpasswd
```

### WR-02: Usuário admin CUPS adicionado ao grupo `root`

**File:** `cups/entrypoint.sh:21`  
**Issue:** `useradd -G lpadmin,sys,root` concede membership no grupo `root` desnecessariamente. Comprometimento da conta admin CUPS amplia superfície de ataque (acesso a arquivos grupo-root dentro do container).

**Fix:** Remover `root` do `-G`: `useradd -r -G lpadmin,sys "${CUPS_ADMIN_USER}"`.

### WR-03: Validação CIDR aceita valores inválidos ou excessivamente amplos

**File:** `cups/entrypoint.sh:9`  
**Issue:** Regex `^[0-9./]+$` aceita strings como `10.0.0.0/8` ou `999.999.999.999/99`. O primeiro alargaria ACL para toda a rede `10.0.0.0/8`, violando D-06/D-08; o segundo pode passar no regex mas falhar silenciosamente ou gerar comportamento imprevisível no `cupsd`.

**Fix:** Validar formato CIDR estrito (octetos 0–255, prefixo 0–32) antes do `envsubst`, ou usar helper dedicado (`ipcalc`, Python `ipaddress`).

### WR-04: Porta 631 publicada em todas as interfaces do host

**File:** `docker-compose.yml:7-8`  
**Issue:** Mapeamento `"631:631"` equivale a `0.0.0.0:631` no host. A ACL CUPS filtra por IP de cliente, mas não restringe em quais interfaces o daemon escuta no host. VM com múltiplas NICs ou rota indevida expõe CUPS além da LAN `REDACTED_LAN` pretendida.

**Fix:** Bind explícito à interface da VM:
```yaml
ports:
  - "VM_HOST:631:631"
```

### WR-05: `validate-phase1.sh` hardcodeia ACL `REDACTED_IP/16` ignorando `.env`

**File:** `scripts/validate-phase1.sh:181-185`  
**Issue:** O check runtime faz `grep 'Allow from REDACTED_IP/16'` em vez de ler `ALLOWED_NETWORK` do `.env`. Se a variável for customizada (mesmo dentro de requisitos futuros), o teste falha incorretamente ou passa enquanto a config real difere — falso positivo/negativo operacional.

**Fix:** Carregar `ALLOWED_NETWORK` do `.env` e usar no grep dinâmico:
```bash
allowed="$(grep -E '^ALLOWED_NETWORK=' .env | cut -d= -f2-)"
docker compose exec -T cups grep -qF "Allow from ${allowed}" /etc/cups/cupsd.conf
```

### WR-06: Inconsistência de máscara de rede na documentação

**File:** `docs/vm-deploy-runbook.md:29` vs `docs/vm-setup.md:36-46`  
**Issue:** O runbook mostra evidência `VM_HOST/24` enquanto vm-setup e decisões D-17 especificam `/16`. Operador pode aplicar netplan com máscara errada, quebrando roteamento ou ACL percebida.

**Fix:** Padronizar `/16` em todos os exemplos e corrigir a linha 29 do runbook para `VM_HOST/16`.

## Info

### IN-01: `Browsing On` expõe descoberta mDNS desnecessária

**File:** `cups/cupsd.conf.template:8-9`  
**Issue:** `Browsing On` + `BrowseLocalProtocols dnssd` anuncia impressoras via DNS-SD na rede. Para print server corporativo fixo (IPP URL documentada), aumenta superfície de descoberta sem benefício claro na Fase 1.

**Fix:** Considerar `Browsing Off` até haver requisito de auto-discovery.

### IN-02: `verify-vm-network.sh` executa grep ACL duplicado com saída não formatada

**File:** `scripts/verify-vm-network.sh:95-98`  
**Issue:** O `if` imprime saída crua do primeiro `grep | head -5` e depois repete o mesmo comando com `sed`. Output redundante e confuso para operador.

**Fix:** Remover o primeiro `grep` do condicional; manter apenas o bloco formatado com `sed`.

---

_Reviewed: 2026-05-26T12:00:00Z_  
_Reviewer: Claude (gsd-code-reviewer)_  
_Depth: standard_
