# Contributing to PrintWatch

## Open-Source Hygiene Policy

PrintWatch é um projeto de monitoramento de impressão com objetivo de ser totalmente open-source.
Para proteger dados operacionais e credenciais de quem usa o projeto, **nunca commite dados reais de infraestrutura**.

---

### O que nunca deve entrar no repositório

| Categoria | Exemplos | Regra |
|---|---|---|
| IPs de produção | `192.168.1.10`, `10.0.0.5` | Usar placeholders (ver abaixo) |
| Hostnames reais | `printwatch-corp.local`, `server01` | Usar `<VM_HOST>` ou nome genérico |
| Usernames reais | `joao.silva`, `admin-prod` | Usar `user.example` em fixtures/docs |
| Nomes de domínio AD | `ACME`, `CORP` | Usar `DOMAIN` como placeholder |
| Senhas/credenciais | qualquer senha real | Nunca — use `.env` local (não commitado) |
| Chaves SSH/TLS | `id_rsa`, `*.pem`, `*.key` | Nunca — geradas localmente |
| IPs de impressoras | `192.168.1.50` | Usar `<PRINTER_HOST>` |
| Logs com dados reais | `page_log` bruto do servidor | Nunca commitar — usar sintéticos |
| Dumps de banco | `*.db`, `*.sqlite` | Ignorado por `.gitignore` |

---

### Placeholders aprovados

| Contexto | Placeholder a usar |
|---|---|
| IP de servidor/VM | `<VM_HOST>` ou `192.0.2.10` (TEST-NET RFC 5737) |
| IP de cliente Windows | `<CLIENT_HOST>` ou `192.0.2.20` |
| IP de impressora | `<PRINTER_HOST>` ou `192.0.2.50` |
| Gateway/DNS | `<NETWORK_GATEWAY>` |
| Range de rede | `<ALLOWED_NETWORK>` |
| Username real | `user.example` |
| Username com domínio AD | `DOMAIN\user.example` |
| Admin SSH | `admin-user` |

**Faixas IP recomendadas para fixtures e exemplos:**
- `192.0.2.0/24` — TEST-NET-1 (RFC 5737) — nunca roteável
- `198.51.100.0/24` — TEST-NET-2 (RFC 5737)
- `203.0.113.0/24` — TEST-NET-3 (RFC 5737)

---

### Arquivos de investigação e evidência

Arquivos com traces reais, dumps de banco, linhas brutas de `page_log`, ou qualquer dado
de produção **devem ser mantidos apenas localmente** e nunca commitados.

O `.gitignore` já exclui automaticamente:

```
.planning/phases/**/*INVESTIGATION*.md
.planning/phases/**/*EVIDENCE*.md
.planning/phases/**/*DUMP*.md
.planning/phases/**/*TRACE*.md
```

Se precisar documentar uma investigação, use o arquivo de investigação localmente
e faça referência apenas a **padrões sintéticos** nos commits.

---

### Fixtures de testes

Fixtures em `tests/conftest.py` e arquivos de teste devem usar apenas dados sintéticos:

```python
# CORRETO — TEST-NET RFC 5737
PrintJob(printer="test_printer", username="DOMAIN\\user.example", host_origin="192.0.2.1")

# ERRADO — IP real
PrintJob(printer="my-printer", username="joao.silva", host_origin="10.0.1.50")
```

---

### Configuração de ambiente

1. Copie `.env.example` para `.env`: `cp .env.example .env`
2. Edite `.env` com seus valores reais (não commitado — protegido por `.gitignore`)
3. **Nunca** coloque valores reais em `.env.example` — use apenas placeholders

---

### Pre-commit (obrigatório em cada clone)

Ative os hooks versionados no repositório (bloqueia IPs da rede corporativa e usuários reais em arquivos staged):

```bash
git config core.hooksPath .githooks
```

Validação manual antes do commit:

```powershell
# Windows
.\scripts\check-no-secrets.ps1 --staged

# Linux / Git Bash
./scripts/check-no-secrets.sh --staged
```

### Re-sanitizar histórico Git (raro)

Se dados reais entraram no histórico:

1. Copie `replacements-filter-repo.example.txt` → `replacements.txt` (local, gitignored)
2. `pip install git-filter-repo`
3. `git filter-repo --replace-text replacements.txt --force`
4. `git remote add origin <url>` e `git push --force-with-lease origin master`

**Aviso:** force-push reescreve o histórico para todos os colaboradores.

---

### Nota sobre `host_origin` na API

O campo `host_origin` em `/api/v1/jobs` expõe o IP do cliente que enviou o job de impressão.
Isso é **intencional** para fins de auditoria de impressão, mas implica responsabilidades:

- Em ambientes corporativos, pode identificar máquinas e usuários (relevante LGPD/GDPR)
- O operador é responsável por controlar o acesso à API (autenticação, rede, VPN)
- Não exponha a porta `8000` diretamente na internet — use reverse proxy com autenticação

---

### Checklist antes de cada commit

- [ ] Não contém IPs reais de produção
- [ ] Não contém usernames reais de funcionários
- [ ] Não contém nomes de domínios AD corporativos
- [ ] Não contém hostnames de servidores internos
- [ ] `.env` não foi incluído no `git add`
- [ ] Arquivos `*INVESTIGATION*.md` locais não foram incluídos
- [ ] Fixtures de teste usam dados sintéticos (RFC 5737 ou placeholders)
