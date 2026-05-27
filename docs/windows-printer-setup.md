# Impressoras no Windows e no PrintWatch

Guia operacional para **cadastrar uma nova impressora** no sistema e para **usar uma impressora já cadastrada** no painel PrintWatch a partir de um PC Windows.

Há **três camadas** independentes — todas precisam estar alinhadas:

| Camada | Onde | Função |
|--------|------|--------|
| **PrintWatch** | Painel web → Configurações → Impressoras | Cadastro mestre (nome, fila CUPS, IP físico, departamento) |
| **CUPS (VM)** | Servidor PrintWatch | Fila que recebe jobs do Windows e encaminha à impressora física |
| **Windows** | PC do usuário | Atalho de impressão apontando para a fila na VM |

O nome da fila CUPS (`cups_queue_name`) deve ser **idêntico** nos três lugares.

---

## Adicionar impressora no Windows (caminho correto)

### O que não usar

No assistente **Adicionar impressora**, **não** escolha:

- **“Selecionar uma impressora compartilhada pelo nome”**

Esse caminho procura impressoras publicadas no estilo `\\servidor\impressora` (SMB). O PrintWatch expõe filas via **IPP na porta 631**, não como compartilhamento SMB. Com o caminho errado, o Windows pode não listar a fila, usar driver inadequado ou falhar em silêncio.

### O que usar

1. **Configurações** → **Bluetooth e dispositivos** → **Impressoras e scanners**
2. **Adicionar dispositivo** → **Adicionar manualmente**
3. Selecione **“Adicionar uma impressora usando um endereço TCP/IP ou nome de host”**
4. Tipo de dispositivo: **Dispositivo TCP/IP** (ou **Internet Printing Protocol (IPP)** se o assistente oferecer)
5. **Nome do host ou endereço IP:** cole a URL completa da fila (veja abaixo)
6. Marque **“Consultar a impressora e selecionar o driver automaticamente”** se disponível; senão escolha o driver manualmente (seção [Driver](#driver-no-windows))
7. Conclua o assistente

### URL da impressora (impressora já cadastrada no PrintWatch)

No painel: **Configurações → Impressoras** → coluna **Fila CUPS** (`cups_queue_name`).

Monte a URL:

```text
http://<IP-OU-HOST-DA-VM>:631/printers/<cups_queue_name>
```

Exemplo (substitua pelos valores reais):

```text
http://VM_HOST:631/printers/colorida_corredor
```

- `<IP-OU-HOST-DA-VM>` — servidor onde roda `docker compose` (PrintWatch)
- `<cups_queue_name>` — exatamente como no cadastro (minúsculas, underscores, sem espaços)

### Driver no Windows

| Evitar | Preferir |
|--------|----------|
| Generic / **Text Only** | **Samsung X4300 Series** (ou modelo da família da sua máquina) |
| | **Microsoft PWG Raster Class Driver** |
| | Driver Samsung **Universal Print** |

**Generic / Text Only** não oferece cor e pode gerar jobs só em preto e branco.

Depois de instalar: **Preferências de impressão** → modo **Cor / Color** (não “Escala de cinza”). Teste com **PDF ou imagem colorida**, não só “página de teste” do Windows.

---

## Usar impressora já cadastrada no PrintWatch

Checklist rápido para quem só vai **imprimir** (fila já existe no painel e na VM):

1. Anote no painel o **`cups_queue_name`** (ex.: `colorida_corredor`).
2. Confirme na VM que a fila CUPS existe:
   ```bash
   ssh admin-user@VM_HOST
   cd ~/printwatch
   docker compose exec -T cups lpstat -p
   docker compose exec -T cups lpstat -v <cups_queue_name>
   ```
3. No Windows, adicione a impressora pelo caminho [**TCP/IP ou nome de host**](#adicionar-impressora-no-windows-caminho-correto) com a URL `http://VM_HOST:631/printers/<cups_queue_name>`.
4. Imprima um documento colorido de teste.
5. Confirme no dashboard PrintWatch se o job aparece (pode levar alguns segundos).

Se a fila **não** aparecer no `lpstat -p`, peça ao administrador para criar a fila na VM (próxima seção) antes de configurar o Windows.

---

## Cadastrar uma nova impressora no sistema (administrador)

Fluxo completo para uma impressora nova na rede.

### 1. Cadastro no painel PrintWatch

1. Acesse `http://<VM_HOST>/` (ou URL do nginx do ambiente).
2. **Configurações → Impressoras** → **Nova impressora**.
3. Preencha:

   | Campo | Orientação |
   |-------|------------|
   | **Nome de exibição** | Nome amigável (ex.: “Colorida 2º Piso”) |
   | **Fila CUPS** (`cups_queue_name`) | Nome técnico da fila, **sem espaços** (ex.: `colorida_corredor`). Será usado na URL Windows e no CUPS. |
   | **Endereço IP** | IP da impressora física na LAN (referência; o CUPS usa a URI IPP) |
   | **Fabricante / modelo** | Ex.: Samsung X4220RX |
   | **Localização** | Opcional |
   | **Departamento** | Opcional |

4. Salve.

Se o watcher detectar jobs em fila ainda não cadastrada, o banner **Filas não mapeadas** permite criar o cadastro com o nome da fila já sugerido.

### 2. Criar a fila no CUPS (VM)

SSH na VM (`~/printwatch`).

**Impressora de teste / `.env` (`TEST_PRINTER_*`):**

```bash
./scripts/setup-printer.sh
docker compose exec -T cups lpstat -p
```

**Impressora de produção** (nome e IP do passo 1):

```bash
# URI com porta :631 (obrigatório para Samsung/HP na prática)
QUEUE=colorida_corredor
URI=ipp://<IP_IMPRESSORA>:631/ipp/print

docker compose exec -T cups lpadmin -p "$QUEUE" -v "$URI" \
  -m openprinting-ppds:0/ppd/openprinting/Samsung/PS/Samsung_X4300_Series.ppd -E
docker compose exec -T cups lpoptions -p "$QUEUE" -o ColorModel=Color
docker compose exec -T cups lpadmin -p "$QUEUE" -o printer-error-policy=abort-job
docker compose exec -T cups cupsaccept "$QUEUE"
docker compose exec -T cups cupsenable "$QUEUE"
docker compose exec -T cups lpstat -p "$QUEUE"
```

Ou use o script (após `git pull`):

```bash
chmod +x scripts/fix-cups-color-queue.sh
./scripts/fix-cups-color-queue.sh <cups_queue_name> ipp://<IP_IMPRESSORA>:631/ipp/print
```

**Importante:** `cups_queue_name` no painel = nome da fila no `lpadmin -p`.

### 3. Configurar PCs Windows

Para cada estação:

- Siga [Adicionar impressora no Windows](#adicionar-impressora-no-windows-caminho-correto).
- URL: `http://<VM_HOST>:631/printers/<cups_queue_name>`.

### 4. Verificação

```bash
# Job de teste na VM
docker compose exec -T cups lp -d <cups_queue_name> -o ColorModel=Color \
  /usr/share/cups/data/default-testpage.pdf

# Última linha no log
docker compose exec -T cups grep '<cups_queue_name>' /var/log/cups/page_log | tail -1
```

No painel: job listado em **Trabalhos** com a impressora correta.

---

## Política de acesso (Fase 5.2)

Se o administrador restringiu usuários por impressora (**Configurações → Usuários → acesso a impressoras**), jobs fora da política ainda podem imprimir fisicamente, mas aparecem marcados no relatório. Isso não altera o cadastro da fila no Windows.

---

## Problemas comuns

| Sintoma | Causa provável | Ação |
|---------|----------------|------|
| Assistente não acha a impressora | Caminho “compartilhada pelo nome” | Usar **TCP/IP ou nome de host** + URL `http://…:631/printers/…` |
| Só imprime P&B | Driver Generic Text Only ou fila CUPS em mono | Driver Samsung/PWG; `ColorModel=Color` na VM; ver [fix-cups-color-queue.sh](../scripts/fix-cups-color-queue.sh) |
| Job na UI, nada na impressora | Fila CUPS ausente ou jobs presos | `lpstat -p`; `docker compose exec cups cancel -a <fila>` |
| `unknown destination` no cancel | Fila não existe no CUPS | Recriar fila (seção 2) |
| Impressora recriada no Docker | Volume CUPS não guarda filas | Rodar `setup-printer.sh` ou `lpadmin` de novo após `docker compose up` |

---

## Referências

- [vm-setup.md](vm-setup.md) — preparação da VM e `setup-printer.sh`
- [vm-deploy-runbook.md](vm-deploy-runbook.md) — deploy e checklist de rede (porta 631)
- [phase1-validation.md](phase1-validation.md) — validação job remoto e `page_log`
- [scripts/setup-printer.sh](../scripts/setup-printer.sh) — fila de teste idempotente
- [scripts/fix-cups-color-queue.sh](../scripts/fix-cups-color-queue.sh) — fila Samsung com cor
