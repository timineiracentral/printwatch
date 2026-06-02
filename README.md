# PrintWatch

Servidor de impressão intermediário com CUPS — registra jobs no `page_log` para auditoria de impressões na rede corporativa.

## Fase 1 (atual)

Valida a cadeia **Docker Compose → CUPS → impressora → `page_log`**. Dashboard e backend entram nas Fases 2–4.

**Guia completo de deploy na VM:** [docs/vm-setup.md](docs/vm-setup.md)

## Quick start

```bash
cp .env.example .env
# Edite .env: CUPS_ADMIN_PASSWORD e TEST_PRINTER_URI (IP real da impressora)
docker compose up -d --build
./scripts/setup-printer.sh
bash scripts/validate-phase1.sh --quick
```

### Impressora de teste

- **Com hardware:** configure `TEST_PRINTER_URI=ipp://192.0.2.50/ipp/print` e `TEST_PRINTER_DRIVER=everywhere`
- **Sem hardware (dev):** deixe o placeholder no URI — o script usa fallback `cups-pdf` automaticamente

## Estrutura

```
printwatch/
├── docker-compose.yml    # Fase 1: somente CUPS
├── cups/                 # Dockerfile, cupsd.conf, entrypoint
├── scripts/
│   ├── setup-printer.sh  # Cadastro idempotente lpadmin
│   └── validate-phase1.sh
└── docs/vm-setup.md      # Checklist VM VM_HOST
```

## Documentação

- [PRD.md](PRD.md) — visão do produto
- [SPEC.md](SPEC.md) — especificação técnica
- [docs/vm-setup.md](docs/vm-setup.md) — preparação da VM Ubuntu 22.04
- [docs/windows-printer-setup.md](docs/windows-printer-setup.md) — cadastrar impressora (painel + CUPS + Windows) e usar fila já cadastrada
- [docs/cups-color-capture.md](docs/cups-color-capture.md) — runbook PB vs color no `page_log`
- [.planning/research/CUPS-COLOR-CAPTURE.md](.planning/research/CUPS-COLOR-CAPTURE.md) — pesquisa CUPS/Context7 (mapeamento, decisão `%{print-color-mode}`)

## Próximas fases

| Fase | Entrega |
|------|---------|
| 2 | Backend log-watcher + parser `page_log` |
| 3–4 | Dashboard e API |
| 5 | UI de cadastro de impressoras |
