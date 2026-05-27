# Reescrita de histórico Git (segurança)

Se o repositório passou por `git filter-repo` para remover IPs/usuários reais:

## Colaboradores com clone antigo

```bash
cd printwatch
git fetch origin
git reset --hard origin/master
```

Se `reset` falhar ou o histórico local conflitar, **reclone**:

```bash
git clone https://github.com/timineiracentral/printwatch.git
```

## VM de deploy (Linux)

```bash
ssh admin-user@VM_HOST
cd ~/printwatch
git fetch origin
git reset --hard origin/master
docker compose up -d --build
```

## Prevenção

```bash
git config core.hooksPath .githooks
```

Antes de cada commit: `.\scripts\check-no-secrets.ps1 --staged`
