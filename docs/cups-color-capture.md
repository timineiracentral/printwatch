# Captura de modo de cor no CUPS (page_log)

Runbook operacional para classificar impressões como **mono** ou **color** na captura (`color_mode_source=captured`).

**Documentação técnica completa** (pesquisa Context7, mapeamento de campos, decisões):  
[`.planning/research/CUPS-COLOR-CAPTURE.md`](../.planning/research/CUPS-COLOR-CAPTURE.md)

---

## Visão rápida

| O quê | Detalhe |
|-------|---------|
| Fonte da verdade | Atributo IPP **`print-color-mode`** no job |
| Como chega ao PrintWatch | Linha do `page_log` → parser (`parser.py`, grupo 6) → `normalize_color_mode()` |
| Formato recomendado | `%{print-color-mode}` no `PageLogFormat` (substitui `%{job-billing}` na mesma posição) |
| **Não** é cor | Sequência `%C` do CUPS = **cópias**, não PB/color |

---

## Pré-requisitos

- Docker Compose com serviço **cups** em execução.
- Driver/fila com **page accounting** (contagem de páginas no log).
- Nome da fila CUPS e URI IPP da impressora.

---

## Passo 1 — `PageLogFormat` (uma vez por ambiente)

No container, o template do repositório é aplicado via `cups/cupsd.conf.template`. O formato **recomendado** (Fase 9 — já no template):

```text
PageLogFormat "%p %u %j %T %P %C %{print-color-mode} %{job-originating-host-name} %{job-name} %{media} %{sides}"
```

Após alterar o template:

```bash
docker compose build cups && docker compose up -d cups
```

Conferir que `%{print-color-mode}` está ativo (não `%{job-billing}`):

```bash
docker compose exec cups grep PageLogFormat /etc/cups/cupsd.conf
```

---

## Pós-deploy template (Fase 9)

Após merge ou alteração em `cups/cupsd.conf.template`:

1. **Rebuild e restart do container CUPS:**

   ```bash
   docker compose build cups && docker compose up -d cups
   ```

2. **Verificar `PageLogFormat`** contém `%{print-color-mode}` (campo 6 do parser — **não** `%{job-billing}`):

   ```bash
   docker compose exec cups grep PageLogFormat /etc/cups/cupsd.conf
   ```

3. **Imprimir job de teste** (após configurar fila — ver Passo 2):

   ```bash
   docker compose exec cups lp -d <nome_fila> /usr/share/cups/data/default-testpage.pdf
   ```

4. **Validar `page_log`** — campo 6 deve conter valor IPP (`monochrome`, `color`, `auto`, etc.), não vazio:

   ```bash
   docker compose exec cups tail -5 /var/log/cups/page_log
   ```

   Critério: na nova linha, o **6º campo** (após `total <N>`) contém valor IPP — não `-` nem vazio após job de teste.

5. **Filas Samsung com PPD mono forçado:** usar `scripts/fix-cups-color-queue.sh` (ver Passo 2).

---

## Mapeamento print-color-mode → color_mode

Valores IPP no campo 6 do `page_log` e como o PrintWatch classifica (`color_mode.py`, `_MONO_ALIASES`):

| Valor IPP (page_log campo 6) | color_mode | color_mode_source | Notas |
|------------------------------|------------|-------------------|-------|
| auto-monochrome, process-monochrome, bi-level, color-monochrome, monochrome, gray | mono | captured | aliases em `_MONO_ALIASES` |
| color | color | captured | |
| auto | NULL | NULL | ambíguo — permanece pendente |
| (vazio/desconhecido) | NULL | NULL | pendente até correção manual |

---

## Passo 2 — Configurar fila

Evita PPD Samsung com `print-color-mode=monochrome` fixo:

```bash
./scripts/fix-cups-color-queue.sh <nome_fila> <uri_ipp>
```

Exemplo:

```bash
./scripts/fix-cups-color-queue.sh colorida_corredor ipp://REDACTED_LAN:631/ipp/print
```

O script: recria fila, `ColorModel=Color`, remove `monochrome` forçado, reativa fila.

Teste:

```bash
docker compose exec cups lp -d <nome_fila> /usr/share/cups/data/default-testpage.pdf
```

---

## Passo 3 — Validar `page_log`

Formato da linha (campos principais):

```text
<impressora> <usuario> <job_id> [<timestamp>] total <paginas> <print-color-mode> <host> <job_name> <media> <sides>
```

Inspecionar:

```bash
docker compose exec cups tail -n 20 /var/log/cups/page_log
```

O **6º campo** (após `total <N>`) deve ser `monochrome` ou `color`, não apenas `-`.

| Valor no log | `color_mode` no banco |
|--------------|------------------------|
| `monochrome`, `grayscale`, `gray`, … | `mono` |
| `color`, `rgb`, `cmyk`, … | `color` |
| `-` ou desconhecido | NULL (pendente) |

---

## Passo 4 — Validar no painel / API

- UI **Jobs**: colunas mono/color e custo (Fase 6).
- API: `GET /api/v1/jobs` — `pages_mono`, `pages_color`, `pages_pending_color`.

---

## Páginas pendentes e correção manual

`color_mode` NULL → não entra em custo faturável até resolução.

Na Fase 6, admin corrige na auditoria (`PATCH` → `color_mode_source=manual`). Priorize corrigir CUPS quando muitas linhas ficam pendentes no mesmo período.

---

## Checklist VM (go-live Fase 6/7)

- [ ] `PageLogFormat` com `%{print-color-mode}` ativo no container
- [ ] `fix-cups-color-queue.sh` na fila de produção
- [ ] Impressão teste mono → campo 6 = `monochrome` (ou alias mono)
- [ ] Impressão teste color → campo 6 = `color`
- [ ] Jobs na UI com `color_mode_source=captured` (não só manual)

---

## Referências

| Recurso | Caminho |
|---------|---------|
| Pesquisa e decisão | `.planning/research/CUPS-COLOR-CAPTURE.md` |
| Template CUPS | `cups/cupsd.conf.template` |
| Script fila | `scripts/fix-cups-color-queue.sh` |
| Parser | `backend/app/services/parser.py` |
| Aliases | `backend/app/services/color_mode.py` |
| Fase 6 (produto) | `.planning/phases/06-costing-chargeback/06-CONTEXT.md` |
