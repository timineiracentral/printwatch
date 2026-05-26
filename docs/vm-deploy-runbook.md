# Runbook — Deploy PrintWatch na VM (VM_HOST)

Sequência operacional para implantar o CUPS da Fase 1 na VM Ubuntu 22.04 no XCP-ng. Este runbook cobre o que o operador executou manualmente em 2026-05-26 e o caminho automatizado via scripts.

**VM alvo:** `admin-user@VM_HOST` (hostname `printwatch`)  
**Rede:** `REDACTED_IP/16` — porta **631/tcp** publicada para CUPS

---

## Pré-requisitos

- VM Ubuntu **22.04** existente no XCP-ng (reutilizar — D-16)
- Acesso **SSH** com usuário **sudo**
- IP estático **VM_HOST/16** (ver [vm-setup.md](vm-setup.md) §1–2)
- Impressora na LAN ou fallback `cups-pdf` (placeholder em `.env`)

---

## Passo 1 — Acesso SSH

```bash
ssh admin-user@VM_HOST
```

Confirme hostname e IP:

```bash
hostname   # printwatch
ip addr show eth0 | grep 'inet '   # VM_HOST/24
```

---

## Passo 2 — Hostname e IP estático

Se ainda não configurado, siga [vm-setup.md §1–2](vm-setup.md#1-hostname):

- `sudo hostnamectl set-hostname printwatch`
- Netplan com `VM_HOST/16` → `sudo netplan apply`

---

## Passo 3 — Clone do repositório e `.env`

```bash
git clone <url-do-repositorio> printwatch
cd printwatch
cp .env.example .env
nano .env   # ou vim
```

| Variável | Ação obrigatória |
|----------|------------------|
| `CUPS_ADMIN_PASSWORD` | **Substituir** `changeme` |
| `TEST_PRINTER_URI` | IP real (`ipp://PRINTER_HOST/ipp/print`) ou placeholder para cups-pdf |
| `TEST_PRINTER_DRIVER` | `everywhere` (IPP) ou driver cups-pdf |

> O bootstrap **aborta** se `CUPS_ADMIN_PASSWORD=changeme`.

---

## Passo 4 — Bootstrap automatizado

```bash
chmod +x scripts/bootstrap-vm.sh scripts/verify-vm-network.sh scripts/setup-printer.sh
./scripts/bootstrap-vm.sh
```

**O que o script faz:**

1. Valida Ubuntu 22.04 e avisa se IP ≠ VM_HOST
2. **Docker:** pula instalação se `docker compose` já funciona; caso contrário tenta `apt install docker.io docker-compose-plugin`
3. **Conflito containerd:** se `apt docker.io` falhar por conflito com Docker CE já instalado, mantém o Docker existente (não force `docker.io` sobre `containerd.io`)
4. `docker compose up -d --build` e aguarda CUPS HTTP (120s)
5. `./scripts/setup-printer.sh`
6. `bash scripts/validate-phase1.sh --quick`

Flags úteis:

```bash
./scripts/bootstrap-vm.sh --skip-docker-install   # Docker CE já instalado (recomendado na VM printwatch)
./scripts/bootstrap-vm.sh --dry-run               # apenas echo, sem mutação
```

**Evidência deploy 2026-05-26:** Docker Compose v5.1.3 pré-instalado; `apt docker.io` falhou por conflito containerd — stack subiu com Docker CE existente.

---

## Passo 5 — Verificação de rede

Na VM:

```bash
./scripts/verify-vm-network.sh
```

De **outro host** na rede `REDACTED_LAN` (ex.: PC Windows):

```bash
curl -I http://VM_HOST:631/
# Esperado: HTTP/1.1 200 OK
```

Opcional na VM:

```bash
./scripts/verify-vm-network.sh --from-ip REDACTED_IP
```

---

## Passo 6 — Gate de prontidão (antes de phase1-validation)

Checklist antes de retomar **01-04 Task 3** (job remoto IPP Windows):

| # | Verificação | Comando | Esperado |
|---|-------------|---------|----------|
| 1 | Container CUPS | `docker compose ps` | `printwatch-cups-1` running, `0.0.0.0:631->631/tcp` |
| 2 | HTTP local | `curl -I http://127.0.0.1:631/` | HTTP 200 |
| 3 | HTTP LAN | `curl -I http://VM_HOST:631/` (de outro host) | HTTP 200 |
| 4 | Impressora | `docker compose exec -T cups lpstat -p` | `test_printer` enabled |
| 5 | URI | `docker compose exec -T cups lpstat -v test_printer` | URI real ou cups-pdf |
| 6 | Smoke | `bash scripts/validate-phase1.sh --quick` | 0 FAIL, exit 0 |

**Evidência operador 2026-05-26:**

- `test_printer` → `ipp://PRINTER_HOST/ipp/print` (driver `everywhere`)
- `validate-phase1.sh --quick` → **17 PASS**, 0 FAIL, 0 WARN

---

## Passo 7 — Próximo passo (desbloqueio 01-04)

Com o gate verde, retome o checkpoint **01-04 Task 3**:

1. Leia [phase1-validation.md §2](phase1-validation.md) — job remoto IPP desde Windows
2. Adicione impressora IPP `http://VM_HOST:631/printers/test_printer` no PC cliente
3. Envie job de teste e valide linha em `page_log` com `DOMINIO\usuario`

---

## Troubleshooting

### `apt install docker.io` falha (containerd conflict)

**Causa:** Docker CE já instalado com `containerd.io`; pacote `docker.io` do Ubuntu conflita.

**Ação:** Use `./scripts/bootstrap-vm.sh --skip-docker-install` ou confirme `docker compose version` antes do bootstrap. **Não** remova containerd.io só para instalar docker.io do apt.

### Bootstrap aborta em `.env`

Edite `.env` e defina `CUPS_ADMIN_PASSWORD` diferente de `changeme`.

### CUPS timeout após compose up

```bash
docker compose logs cups --tail 50
docker compose exec -T cups cupsd -t
```

### Firewall

- `ufw` na VM: regra `631/tcp` se ativo
- Firewall corporativo / hypervisor: liberar 631 de `REDACTED_IP/16` → `VM_HOST`

---

## Referências

- [vm-setup.md](vm-setup.md) — preparação manual (hostname, netplan, cadastro manual)
- [phase1-validation.md](phase1-validation.md) — validação E2E job local + IPP remoto
- [README.md](../README.md) — quick start geral
