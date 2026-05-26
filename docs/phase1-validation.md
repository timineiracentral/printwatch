# Validação E2E — Fase 1 (PrintWatch)

Procedimento operacional para validar a cadeia **Docker Compose → CUPS → impressora → `page_log`**, conforme decisões D-13, D-14 e D-17.

**VM alvo:** `VM_HOST` (hostname `printwatch`)

---

## Seção 1 — Job local (automático)

A validação local (D-13 modo 1) é executada automaticamente pelo script de smoke tests:

```bash
bash scripts/validate-phase1.sh
```

**O que o script faz:**

1. Pré-checks estáticos (compose, `.env.example`, ACL, PageLogFormat)
2. Verifica container `cups` running
3. Envia job via `lp` dentro do container com `-U 'DOMINIO\usuario'`
4. Aguarda 3 segundos e valida a última linha de `/var/log/cups/page_log` contra `PAGE_LOG_REGEX` (SPEC §3.2)
5. Confirma nome da impressora (`TEST_PRINTER_NAME`), username com backslash e timestamp parseável

**Modo rápido** (sem job local, ~30s):

```bash
bash scripts/validate-phase1.sh --quick
```

**Esperado:** exit code `0` e mensagens `[PASS]` para todos os checks.

---

## Seção 2 — Job remoto IPP (D-13.2)

Validação manual obrigatória antes de fechar a Fase 1 — simula o fluxo real de PCs Windows na rede corporativa.

### Pré-requisitos

- PC **Windows** conectado à rede `REDACTED_IP/16`
- Usuário logado com conta **Active Directory**
- Container CUPS rodando na VM (`docker compose ps` → `cups` running)
- Impressora cadastrada (`./scripts/setup-printer.sh`)

### URL IPP (D-17)

```
http://VM_HOST:631/printers/<TEST_PRINTER_NAME>
```

Exemplo com valores padrão do `.env.example`:

```
http://VM_HOST:631/printers/test_printer
```

### Protocolo e driver

- **Protocolo:** IPP (Internet Printing Protocol)
- **Driver:** driver nativo HP/Samsung **ou** **Microsoft IPP Class Driver** (SPEC §6)
- Não usar driver genérico "Text Only" — pode omitir metadados no job

### Passos — adicionar impressora no Windows

1. Abrir **Configurações → Bluetooth e dispositivos → Impressoras e scanners**
2. Clicar **Adicionar dispositivo** → **Adicionar manualmente**
3. Selecionar **Adicionar uma impressora usando um endereço TCP/IP ou nome de host**
4. Tipo de dispositivo: **Dispositivo TCP/IP**
5. Hostname/porta: colar a URL IPP completa (`http://VM_HOST:631/printers/test_printer`)
6. Quando solicitado, escolher driver HP/Samsung ou **Microsoft IPP Class Driver**
7. Concluir o assistente e definir como impressora padrão (opcional)

### Passos — imprimir página de teste

1. Abrir **Bloco de Notas** ou qualquer aplicativo
2. Digitar texto de teste (ex.: `PrintWatch Fase 1 — job remoto IPP`)
3. **Arquivo → Imprimir** → selecionar a impressora IPP adicionada
4. Confirmar impressão estando logado com conta AD (`DOMINIO\usuario`)

---

## Seção 3 — Verificação `page_log` pós-job remoto

Na VM (SSH ou console):

```bash
docker compose exec cups grep '<TEST_PRINTER_NAME>' /var/log/cups/page_log | tail -1
```

Substitua `<TEST_PRINTER_NAME>` pelo valor do `.env` (padrão: `test_printer`).

### Checklist D-14

| Critério | Verificação | Obrigatório |
|----------|-------------|-------------|
| Linha presente | Comando acima retorna pelo menos uma linha | Sim |
| Nome da impressora | Primeiro campo == `TEST_PRINTER_NAME` | Sim |
| Timestamp recente | Campo entre `[` e `]` com data/hora dos últimos ±5 min | Sim |
| Username AD | Formato ideal: `DOMINIO\usuario` | Ideal (D-14) |

**Risco A1 (RESEARCH):** clientes Windows IPP podem enviar username em formato diferente (ex.: `usuario@DOMINIO`, UPN ou SID). Se o campo user **não** for `DOMINIO\usuario`:

1. Anotar o formato observado na linha do `page_log`
2. Confirmar que o campo **não está vazio**
3. Documentar no SUMMARY da Fase 1 para normalização na Fase 2

**Exemplo de linha válida (formato SPEC):**

```
test_printer DOMINIO\usuario 5 [26/May/2026:16:30:00 +0000] total 1 - 192.0.2.50 test-page.pdf - -
```

---

## Seção 4 — ACL (obrigatório no checkpoint)

Confirma SERVER-01 e D-05–D-08: CUPS acessível **somente** da rede `REDACTED_IP/16`.

### Verificar configuração gerada

```bash
docker compose exec -T cups grep 'Allow from' /etc/cups/cupsd.conf
```

**Esperado:** múltiplas entradas `Allow from REDACTED_IP/16` (sem ranges genéricos 192.168/10/172 da SPEC original).

### Teste de acesso HTTP

De um host na rede **REDACTED_LAN** (ex.: PC Windows ou outra VM):

```bash
curl -s -o /dev/null -w "%{http_code}" http://VM_HOST:631/
# Esperado: 200
```

De um host **fora** da faixa `REDACTED_IP/16` (opcional, se disponível):

```bash
curl -s -o /dev/null -w "%{http_code}" http://VM_HOST:631/
# Esperado: 403
```

> No ambiente de dev local (Docker Desktop fora da rede REDACTED_LAN), o teste de bloqueio externo pode não ser reproduzível — executar na VM ou LAN corporativa.

---

## Critérios de aceite da Fase 1

| Modo | Comando / ação | Gate |
|------|----------------|------|
| Local (D-13.1) | `bash scripts/validate-phase1.sh` | Exit 0 |
| Remoto IPP (D-13.2) | Imprimir do Windows + verificar `page_log` | Linha nova obrigatória |
| ACL (SERVER-01) | `grep Allow from` + curl :631 | REDACTED_LAN → 200 |

**Resume signal:** digite `approved` após job remoto IPP validado, ou descreva bloqueio técnico (ex.: sem PC Windows na rede REDACTED_LAN).

---

## Seção 5 — Troubleshooting: impressão física não sai

Se o job remoto IPP aparece no `access_log` e no `page_log`, mas **nada imprime na impressora física**, verifique o URI **backend** (CUPS → impressora), não a URL do cliente Windows.

| Camada | URI / URL correto |
|--------|-------------------|
| Cliente Windows → CUPS | `http://VM_HOST:631/printers/test_printer` |
| CUPS → impressora física (`TEST_PRINTER_URI`) | `ipp://PRINTER_HOST:631/ipp/print` |

**Sintoma:** `page_log` registra o job; `access_log` mostra `successful-ok`; papel não sai.

**Causa comum:** `TEST_PRINTER_URI` sem porta explícita (ex.: `ipp://PRINTER_HOST/ipp/print`).

**Correção na VM:**

```bash
# Editar .env: TEST_PRINTER_URI=ipp://<IP_IMPRESSORA>:631/ipp/print
./scripts/setup-printer.sh
# ou manualmente:
docker compose exec cups lpadmin -p test_printer -v ipp://PRINTER_HOST:631/ipp/print -E
```

Reimprimir página de teste do Windows e confirmar saída física.

---

## Referências

- [scripts/validate-phase1.sh](../scripts/validate-phase1.sh) — suite automatizada
- [docs/vm-setup.md](vm-setup.md) — preparação da VM
- [SPEC.md](../SPEC.md) §3.1 (PageLogFormat), §3.2 (PAGE_LOG_REGEX), §6 (Windows)
- [.planning/phases/01-infrastructure-print-server/01-CONTEXT.md](../.planning/phases/01-infrastructure-print-server/01-CONTEXT.md) — D-13, D-14, D-17
