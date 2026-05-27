# Captura de modo de cor no CUPS (page_log)

Este runbook descreve como maximizar o preenchimento do campo de cor no `page_log` do CUPS, para que o PrintWatch classifique impressões como **mono** ou **color** na captura (`color_mode_source=captured`).

## Pré-requisitos

- Docker Compose com o serviço **cups** em execução (`docker compose ps` deve listar `cups` como `running`).
- Acesso ao host onde o repositório está clonado (para executar scripts na raiz do projeto).
- Nome da fila CUPS e URI IPP da impressora (ex.: `ipp://HOST:631/ipp/print` — use o host real da sua rede; em documentação interna prefira placeholders como `REDACTED_LAN`).

## Configurar fila com impressão colorida

O script `scripts/fix-cups-color-queue.sh` recria a fila com PPD Samsung e força `print-color-mode=color`, evitando que o PPD trave tudo em monocromático.

```bash
./scripts/fix-cups-color-queue.sh <nome_fila> <uri_ipp>
```

Exemplo (substitua host e fila pelos valores do seu ambiente):

```bash
./scripts/fix-cups-color-queue.sh colorida_corredor ipp://REDACTED_LAN:631/ipp/print
```

O script:

1. Verifica se o container `cups` está rodando.
2. Remove/recria a fila com PPD padrão Samsung.
3. Define `ColorModel=Color` e remove `print-color-mode=monochrome` de `printers.conf`.
4. Reativa a fila (`cupsaccept` / `cupsenable`).

Teste rápido após configurar:

```bash
docker compose exec cups lp -d <nome_fila> /usr/share/cups/data/default-testpage.pdf
```

## Validar o page_log

O watcher lê `/var/log/cups/page_log`. Cada linha concluída deve incluir o **6º campo** (modo de cor) com valor reconhecível ou `-` quando ausente.

Formato esperado (campos principais):

```text
<impressora> <usuario> <job_id> [<timestamp>] total <paginas> <cor> ...
```

Valores de `<cor>` mapeados pelo backend:

| CUPS (exemplos) | Canônico |
|-----------------|----------|
| `grayscale`, `gray`, `monochrome`, `bw`, … | `mono` |
| `color`, `rgb`, `cmyk`, … | `color` |
| `-` ou desconhecido | pendente (`NULL`) |

Inspecionar linhas recentes:

```bash
docker compose exec cups tail -n 20 /var/log/cups/page_log
```

Confirme que jobs coloridos exibem um alias de cor (não apenas `-`) após ajuste da fila.

## Páginas pendentes e correção manual

Linhas com `color_mode` **NULL** (campo `-` ou valor não reconhecido) são **páginas pendentes**: não entram em mono/color nem em custo estimado até serem resolvidas.

Na **Fase 6** (custo e chargeback), o administrador pode corrigir manualmente na UI de auditoria (`color_mode_source=manual`). Priorize corrigir a captura CUPS quando muitas linhas ficarem pendentes no mesmo período.

## Referências

- Script: `scripts/fix-cups-color-queue.sh`
- Parser: `backend/app/services/parser.py` + `backend/app/services/color_mode.py`
- Contexto de produto: `.planning/phases/06-costing-chargeback/06-CONTEXT.md` (D-05, D-06)
