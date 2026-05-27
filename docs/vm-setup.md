# Preparação da VM PrintWatch (Fase 1)

Checklist operacional para preparar a VM Ubuntu 22.04 existente no XCP-ng e implantar o serviço CUPS da Fase 1.

> **Deploy automatizado:** para a sequência completa na VM (SSH → clone → bootstrap → rede), use o **[Runbook de deploy](vm-deploy-runbook.md)** com `./scripts/bootstrap-vm.sh` e `./scripts/verify-vm-network.sh`. Este documento cobre **preparação manual** (hostname, netplan, passos equivalentes sem script).

**Objetivo:** chegar a `docker compose up` → impressora cadastrada → fila CUPS pronta para jobs e `page_log`.

---

## Pré-requisitos

- VM **Ubuntu 22.04** já existente no XCP-ng — **reutilizar**, não provisionar nova (D-16)
- Acesso SSH com usuário sudo
- Rede corporativa `REDACTED_IP/16` acessível
- Impressora HP/Samsung na LAN (opcional na Fase 1 — fallback `cups-pdf` para teste sem hardware)

---

## 1. Hostname

Definir hostname `printwatch` (D-18):

```bash
sudo hostnamectl set-hostname printwatch
hostname
# Esperado: printwatch
```

> Se o AD exigir FQDN, ajuste conforme política interna (ex.: `printwatch.empresa.local`).

---

## 2. IP estático

Configurar IP fixo **VM_HOST/16** via netplan (D-17).

Edite `/etc/netplan/00-installer-config.yaml` (nome do arquivo pode variar):

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - VM_HOST/16
      routes:
        - to: default
          via: NETWORK_GATEWAY
      nameservers:
        addresses:
          - NETWORK_GATEWAY
          - 8.8.8.8
```

> **Ajuste o gateway e DNS** para os valores reais da rede REDACTED_LAN — o exemplo acima usa `NETWORK_GATEWAY` como placeholder.

Aplicar:

```bash
sudo netplan apply
ip addr show eth0
# Confirmar: VM_HOST/16
```

---

## 3. Docker e Docker Compose

Instalar Docker na VM (DEPLOY-01):

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin
sudo usermod -aG docker "$USER"
# Re-login ou: newgrp docker
docker compose version
```

---

## 4. Deploy PrintWatch

```bash
git clone <url-do-repositorio> printwatch
cd printwatch
cp .env.example .env
```

Edite `.env`:

| Variável | Ação |
|----------|------|
| `CUPS_ADMIN_PASSWORD` | Substituir `changeme` por senha forte |
| `TEST_PRINTER_URI` | IP real da impressora (`ipp://192.0.2.50/ipp/print`) ou deixar placeholder para fallback cups-pdf |
| `TEST_PRINTER_DRIVER` | `everywhere` (IPP) ou `cups-pdf` (sem hardware) |

Subir CUPS:

```bash
docker compose up -d --build
docker compose ps
# cups deve estar running
```

---

## 5. Cadastro da impressora

Com o container `cups` rodando:

```bash
./scripts/setup-printer.sh
```

Verificar fila:

```bash
docker compose exec -T cups lpstat -p
docker compose exec -T cups lpstat -v test_printer
```

Segunda execução do script deve retornar `already configured` (idempotente, D-11).

Para **filas de produção** (nome diferente de `TEST_PRINTER_NAME`) e **cadastro no painel + Windows**, veja [windows-printer-setup.md](windows-printer-setup.md).

---

## 6. Verificação rápida

```bash
bash scripts/validate-phase1.sh --quick
```

Esperado: exit 0, checks estáticos PASS e checks runtime PASS quando container está up.

---

## Passo manual equivalente ao setup-printer.sh

Para operadores que preferem cadastro manual (D-10), com variáveis do `.env`:

```bash
# Substituir valores conforme .env
PRINTER_NAME=test_printer
PRINTER_URI=ipp://192.0.2.50/ipp/print
PRINTER_DRIVER=everywhere

# Criar ou atualizar impressora
docker compose exec cups lpadmin -p "$PRINTER_NAME" -v "$PRINTER_URI" -m "$PRINTER_DRIVER" -E

# Aceitar jobs e habilitar fila
docker compose exec cups cupsaccept "$PRINTER_NAME"
docker compose exec cups cupsenable "$PRINTER_NAME"

# Confirmar
docker compose exec cups lpstat -p "$PRINTER_NAME"
```

**Fallback sem hardware (cups-pdf):**

```bash
docker compose exec cups lpadmin -p test_printer -v cups-pdf:/ -m lsb/usr/cups-pdf/CUPS-PDF_noopt.ppd -E
docker compose exec cups cupsaccept test_printer
docker compose exec cups cupsenable test_printer
```

**Socket (JetDirect) — Samsung/HP legado:**

```bash
# URI: socket://192.0.2.50:9100 — driver PostScript, não "everywhere"
docker compose exec cups lpadmin -p test_printer -v socket://192.0.2.50:9100 -m postscript-hp:0/ps/hpcups.ppd.gz -E
```

---

## Descoberta de impressora na rede

Para descobrir URIs disponíveis (opcional):

```bash
docker compose exec cups lpinfo -v
```

Documente o IP/URI escolhido em `TEST_PRINTER_URI` no `.env`.

---

## Fora de escopo nesta fase

Conforme D-22, **não** incluir neste checklist:

- Observabilidade / dashboard (Fases 3–4)
- Integração Active Directory (Fase 2+)
- Alta disponibilidade / redundância
- UI web de cadastro de impressoras (Fase 5, SERVER-04)

---

## Referências

- [vm-deploy-runbook.md](vm-deploy-runbook.md) — deploy automatizado na VM VM_HOST
- [README.md](../README.md) — quick start
- [.env.example](../.env.example) — variáveis documentadas (DEPLOY-02)
- [SPEC.md](../SPEC.md) §3.1 — container CUPS e PageLogFormat
- [docs/phase1-validation.md](phase1-validation.md) — validação E2E job local + IPP remoto (D-13, D-14)
