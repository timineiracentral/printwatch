# Phase 2: Log Pipeline & Data Layer — Pattern Map

**Mapeado:** 2026-05-26
**Arquivos analisados:** 14 novos arquivos a criar
**Análogos encontrados:** 8 / 14 (6 sem análogo direto — sem código Python no repo ainda)

---

## Contexto da Análise

O repositório ainda não contém código Python. A Fase 2 é o **primeiro módulo Python** do projeto. Os análogos disponíveis são:

- Scripts bash da Fase 1 (`validate-phase1.sh`, `entrypoint.sh`, `bootstrap-vm.sh`)
- Infraestrutura Docker (`docker-compose.yml`, `cups/Dockerfile`)
- Configuração de ambiente (`.env.example`)

Para os arquivos Python sem análogo no codebase, os padrões provêm de `02-RESEARCH.md` (verificados via Context7 + PyPI).

---

## File Classification

| Arquivo Novo/Modificado | Role | Data Flow | Análogo Mais Próximo | Qualidade |
|-------------------------|------|-----------|----------------------|-----------|
| `backend/Dockerfile` | config | — | `cups/Dockerfile` | role-match |
| `backend/entrypoint.sh` | config | — | `cups/entrypoint.sh` | exact |
| `backend/requirements.txt` | config | — | *(sem análogo — novo)* | none |
| `backend/app/main.py` | provider | request-response | *(sem análogo Python)* | none |
| `backend/app/core/config.py` | config | — | `.env.example` (padrão de variáveis) | partial |
| `backend/app/core/database.py` | config | — | *(sem análogo Python)* | none |
| `backend/app/models/print_job.py` | model | CRUD | *(sem análogo Python)* | none |
| `backend/app/models/capture_state.py` | model | CRUD | *(sem análogo Python)* | none |
| `backend/app/models/policy.py` | model | CRUD | *(sem análogo Python)* | none |
| `backend/app/repositories/print_job_repo.py` | service | CRUD | *(sem análogo Python)* | none |
| `backend/app/services/log_watcher.py` | service | event-driven | *(sem análogo Python)* | none |
| `backend/app/services/tail_reader.py` | service | file-I/O | *(sem análogo Python)* | none |
| `backend/app/services/parser.py` | utility | transform | `scripts/validate-phase1.sh` (PAGE_LOG_REGEX) | partial |
| `backend/app/services/retention.py` | service | batch | *(sem análogo Python)* | none |
| `scripts/validate-phase2.sh` | utility | — | `scripts/validate-phase1.sh` | exact |
| `docker-compose.yml` *(modificar)* | config | — | `docker-compose.yml` atual | exact |
| `.env.example` *(modificar)* | config | — | `.env.example` atual | exact |

---

## Pattern Assignments

### `backend/Dockerfile` (config)

**Análogo:** `cups/Dockerfile`

**Padrão de base e instalação** (`cups/Dockerfile` linhas 1–15):
```dockerfile
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    <pacotes> \
    && rm -rf /var/lib/apt/lists/*

COPY <arquivos> /destino/
RUN chmod +x /script.sh

EXPOSE <porta>

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
```

**Adaptação para backend Python:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

COPY app/ ./app/

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
```

**Diferenças-chave da Fase 2:**
- Base `python:3.11-slim` em vez de `ubuntu:22.04` — Python já incluso
- `pip install` substituindo `apt-get install` para dependências de aplicação
- `WORKDIR /app` — convenção do container backend
- Sem `EXPOSE` (D-12: sem rotas públicas na Fase 2)

---

### `backend/entrypoint.sh` (config)

**Análogo:** `cups/entrypoint.sh` — **match exato de padrão**

**Padrão** (`cups/entrypoint.sh` linhas 1–28):
```bash
#!/bin/bash
set -euo pipefail

# Carregar variáveis de ambiente com defaults
export VARIAVEL="${VARIAVEL:-default}"

# Validação básica de configuração (T-01-04 no CUPS)
if [[ -z "${VARIAVEL}" ]]; then
  echo "VARIAVEL inválida" >&2
  exit 1
fi

# Criar diretórios necessários
mkdir -p /caminho/necessario

# Configuração de runtime (chmod, envsubst, etc.)

# Exec do processo principal (substituir shell)
exec <comando>
```

**Adaptação para backend:**
```bash
#!/bin/bash
set -euo pipefail

DB_PATH="${DB_PATH:-/app/data/printwatch.db}"
LOG_PATH="${LOG_PATH:-/var/log/cups/page_log}"
LOG_RETENTION_DAYS="${LOG_RETENTION_DAYS:-90}"

mkdir -p "$(dirname "$DB_PATH")"

# DATA-03: permissões 600 no SQLite
if [[ -f "$DB_PATH" ]]; then
  chmod 600 "$DB_PATH"
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Padrão crítico herdado:** `exec` (não `&`) garante que o processo é PID 1 → sinais Docker (SIGTERM) chegam ao uvicorn diretamente.

---

### `backend/app/core/config.py` (config)

**Análogo parcial:** `.env.example` — define o vocabulário de variáveis de ambiente

**Variáveis estabelecidas** (`.env.example` linhas 11–23):
```bash
# Fase 1 (existentes)
ALLOWED_NETWORK=REDACTED_IP/16
CUPS_ADMIN_USER=admin
CUPS_ADMIN_PASSWORD=changeme
TEST_PRINTER_NAME=test_printer
TEST_PRINTER_URI=ipp://192.0.2.50/ipp/print
TEST_PRINTER_DRIVER=everywhere
```

**Novas variáveis a adicionar ao `.env.example` (Fase 2):**
```bash
# Fase 2 — backend
DB_PATH=/app/data/printwatch.db
LOG_PATH=/var/log/cups/page_log
LOG_RETENTION_DAYS=90
```

**Padrão de config Python (sem análogo — usar RESEARCH.md):**
```python
import os

class Settings:
    db_path: str = os.environ.get("DB_PATH", "/app/data/printwatch.db")
    log_path: str = os.environ.get("LOG_PATH", "/var/log/cups/page_log")
    log_retention_days: int = int(os.environ.get("LOG_RETENTION_DAYS", "90"))

settings = Settings()
```

---

### `backend/app/core/database.py` (config)

**Análogo:** Nenhum no codebase. Usar padrão verificado de `02-RESEARCH.md` §Padrão 3.

**Padrão de engine SQLAlchemy 2.x com NullPool** (RESEARCH.md linhas 379–386):
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import DeclarativeBase, sessionmaker

class Base(DeclarativeBase):
    pass

engine = create_engine(
    "sqlite:////app/data/printwatch.db",
    connect_args={"check_same_thread": False},
    poolclass=NullPool,
)
SessionLocal = sessionmaker(bind=engine)
```

**Por que NullPool:** Watcher roda em thread daemon separada do FastAPI. QueuePool default do SQLAlchemy mantém conexões abertas que causam `OperationalError: database is locked` em SQLite file-based com múltiplos writers simultâneos (Pitfall 2 do RESEARCH.md).

---

### `backend/app/models/print_job.py` (model, CRUD)

**Análogo:** Nenhum no codebase. Usar padrão verificado de `02-RESEARCH.md` §Padrão 3 + mapeamento PAGE_LOG_REGEX.

**Padrão SQLAlchemy 2.x com Mapped/mapped_column** (RESEARCH.md linhas 344–366):
```python
from sqlalchemy import String, Integer, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from datetime import datetime
from app.core.database import Base

class PrintJob(Base):
    __tablename__ = "print_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Campos diretos do page_log — grupos do PAGE_LOG_REGEX (CAPTURE-01)
    printer: Mapped[str] = mapped_column(String(255), nullable=False)       # grupo 1
    username: Mapped[str] = mapped_column(String(255), nullable=False)      # grupo 2, D-08
    job_id: Mapped[int] = mapped_column(Integer, nullable=False)            # grupo 3
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)   # grupo 4
    pages: Mapped[int] = mapped_column(Integer, nullable=False)             # grupo 5
    color_mode: Mapped[Optional[str]] = mapped_column(String(50))           # grupo 6, D-09
    host_origin: Mapped[Optional[str]] = mapped_column(String(255))        # grupo 7, D-09
    job_name: Mapped[Optional[str]] = mapped_column(String(512))            # grupo 8, D-09
    media: Mapped[Optional[str]] = mapped_column(String(100))               # grupo 9, D-09
    sides: Mapped[Optional[str]] = mapped_column(String(50))                # grupo 10, D-09
    copies: Mapped[Optional[int]] = mapped_column(Integer)                  # não no PageLogFormat atual → NULL
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="allowed")  # EXTEND-01

    __table_args__ = (
        UniqueConstraint("printer", "job_id", "timestamp", "pages", name="uq_page_log_line"),
    )
```

**Regra crítica (D-09):** `Optional[T]` no modelo SQLAlchemy mapeia para coluna nullable. Nunca usar `""` ou `"unknown"` — apenas `None` para campos ausentes.

---

### `backend/app/models/capture_state.py` (model, CRUD)

**Análogo:** Nenhum no codebase. Padrão derivado de `02-RESEARCH.md` §Padrão 3 (D-04).

```python
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class CaptureState(Base):
    __tablename__ = "capture_state"

    id: Mapped[int] = mapped_column(primary_key=True)
    log_path: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    inode: Mapped[int] = mapped_column(Integer, nullable=False)
    byte_offset: Mapped[int] = mapped_column(Integer, nullable=False)
```

**Nota:** `log_path` como chave natural com `unique=True` permite upsert sem subquery adicional (futuro suporte a múltiplos arquivos de log).

---

### `backend/app/models/policy.py` (model, CRUD)

**Análogo:** Nenhum. Tabela vazia no MVP (EXTEND-02).

```python
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.core.database import Base

class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
```

**Coluna mínima agora (Claude's Discretion):** `id + name + created_at` evita migração Alembic na Fase 3. Schema completo de políticas (regras, condições, ações) vem nas Fases 3+.

---

### `backend/app/repositories/print_job_repo.py` (service, CRUD)

**Análogo:** Nenhum no codebase. Padrão de RESEARCH.md §Padrão 4 (idempotência).

**Padrão INSERT OR IGNORE via dialeto SQLite** (RESEARCH.md linhas 396–405):
```python
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session
from app.models.print_job import PrintJob
from app.models.capture_state import CaptureState

def insert_job_idempotent(session: Session, job_dict: dict) -> None:
    stmt = sqlite_insert(PrintJob).values(**job_dict)
    stmt = stmt.on_conflict_do_nothing(
        index_elements=["printer", "job_id", "timestamp", "pages"]
    )
    session.execute(stmt)
    session.commit()

def get_capture_state(session: Session, log_path: str) -> CaptureState | None:
    return session.get(CaptureState, log_path)

def upsert_capture_state(session: Session, log_path: str, inode: int, byte_offset: int) -> None:
    stmt = sqlite_insert(CaptureState).values(
        log_path=log_path, inode=inode, byte_offset=byte_offset
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["log_path"],
        set_={"inode": inode, "byte_offset": byte_offset},
    )
    session.execute(stmt)
    session.commit()
```

**Padrão crítico:** `on_conflict_do_nothing` torna todo INSERT idempotente — ao reprocessar arquivo com inode novo, linhas já no banco são silenciosamente ignoradas (D-06: sem hash de linha).

---

### `backend/app/services/parser.py` (utility, transform)

**Análogo parcial:** `scripts/validate-phase1.sh` — contém o `PAGE_LOG_REGEX` e a lógica de validação dos grupos.

**PAGE_LOG_REGEX do codebase** (`scripts/validate-phase1.sh` linha 20):
```bash
PAGE_LOG_REGEX='^(\S+)\s+(\S+)\s+(\d+)\s+\[(.+?)\]\s+total\s+(\d+)\s+(\S+)\s+(\S+)\s+(.+?)\s+(\S+)\s+(\S+)$'
```

**Mapeamento de grupos** (`validate-phase1.sh` linhas 251–263 + RESEARCH.md §Mapeamento):
- Grupo 1 → `printer`
- Grupo 2 → `username` (manter `DOMINIO\usuario` — D-08)
- Grupo 3 → `job_id` (int)
- Grupo 4 → `timestamp` (parse com `%d/%b/%Y:%H:%M:%S %z`)
- Grupo 5 → `pages` (int)
- Grupo 6 → `color_mode` (NULL se `-`)
- Grupo 7 → `host_origin` (NULL se `-`)
- Grupo 8 → `job_name` (NULL se `-`)
- Grupo 9 → `media` (NULL se `-`)
- Grupo 10 → `sides` (NULL se `-`)

**Padrão de parse Python** (RESEARCH.md linhas 537–562):
```python
import re
from datetime import datetime
from typing import Optional

PAGE_LOG_REGEX = re.compile(
    r'^(\S+)\s+(\S+)\s+(\d+)\s+\[(.+?)\]\s+total\s+(\d+)\s+(\S+)\s+(\S+)\s+(.+?)\s+(\S+)\s+(\S+)$'
)

def _null_if_dash(value: str) -> Optional[str]:
    """D-09: sentinel '-' do CUPS → NULL no banco."""
    return None if value.strip() == "-" else value.strip()

def parse_page_log_line(line: str) -> Optional[dict]:
    m = PAGE_LOG_REGEX.match(line.strip())
    if m is None:
        return None   # linha de status CUPS — descartar silenciosamente
    return {
        "printer":     m.group(1),
        "username":    m.group(2),           # D-08: sem normalização de domínio
        "job_id":      int(m.group(3)),
        "timestamp":   datetime.strptime(m.group(4), "%d/%b/%Y:%H:%M:%S %z"),
        "pages":       int(m.group(5)),
        "color_mode":  _null_if_dash(m.group(6)),
        "host_origin": _null_if_dash(m.group(7)),
        "job_name":    _null_if_dash(m.group(8)),
        "media":       _null_if_dash(m.group(9)),
        "sides":       _null_if_dash(m.group(10)),
        "copies":      None,
        "status":      "allowed",            # D-15, EXTEND-01
    }
```

**Padrão de erro herdado** do `validate-phase1.sh` (linhas 243–248): verificar `if m is None` antes de usar grupos — jamais deixar `AttributeError` propagar e matar o watcher (Pitfall 7 do RESEARCH.md).

---

### `backend/app/services/log_watcher.py` (service, event-driven)

**Análogo:** Nenhum no codebase. Padrão de RESEARCH.md §Padrão 1.

**Padrão InotifyObserver** (RESEARCH.md linhas 244–269):
```python
import time
from watchdog.observers.inotify import InotifyObserver
from watchdog.events import FileSystemEventHandler

class PageLogHandler(FileSystemEventHandler):
    PAGE_LOG_PATH = "/var/log/cups/page_log"

    def __init__(self, tail_reader, processor):
        self._tail = tail_reader
        self._processor = processor

    def on_modified(self, event):
        if not event.is_directory and event.src_path == self.PAGE_LOG_PATH:
            for line in self._tail.read_new_lines():
                self._processor.process(line)

def start_observer(handler) -> InotifyObserver:
    observer = InotifyObserver()
    # CRÍTICO: schedule recebe DIRETÓRIO, não arquivo (Pitfall 1 do RESEARCH.md)
    observer.schedule(handler, path="/var/log/cups", recursive=False)
    observer.start()
    return observer
```

**Integração com FastAPI lifespan** (Claude's Discretion — RESEARCH.md §Open Questions 3):
```python
# backend/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    observer = start_observer(handler)
    yield
    observer.stop()
    observer.join()

app = FastAPI(lifespan=lifespan)
```

---

### `backend/app/services/tail_reader.py` (service, file-I/O)

**Análogo:** Nenhum no codebase. Padrão de RESEARCH.md §Padrão 2 (D-04, D-05).

**Padrão TailReader com checkpoint inode+offset** (RESEARCH.md linhas 283–325):
```python
import os

class TailReader:
    def __init__(self, path: str, state_repo):
        self.path = path
        self._state_repo = state_repo
        self._fh = None
        self._inode = None
        self._offset = 0
        self._recover_checkpoint()

    def _recover_checkpoint(self):
        """Startup: carrega inode+offset do banco (D-05)."""
        state = self._state_repo.get(self.path)
        current_stat = os.stat(self.path)
        current_inode = current_stat.st_ino

        if state and state.inode == current_inode:
            self._inode = current_inode
            self._offset = state.byte_offset
            self._fh = open(self.path, "r", encoding="utf-8", errors="replace")
            self._fh.seek(self._offset)
        else:
            # Inode diferente (logrotate) ou estado inexistente → início do arquivo
            self._inode = current_inode
            self._offset = 0
            self._fh = open(self.path, "r", encoding="utf-8", errors="replace")

    def read_new_lines(self) -> list[str]:
        """Chamado pelo on_modified; retorna novas linhas."""
        current_inode = os.stat(self.path).st_ino
        if current_inode != self._inode:
            # D-05: logrotate detectado → reabrir do início
            self._fh.close()
            self._inode = current_inode
            self._offset = 0
            self._fh = open(self.path, "r", encoding="utf-8", errors="replace")

        lines = self._fh.readlines()
        if lines:
            self._offset = self._fh.tell()
            self._state_repo.upsert(self.path, self._inode, self._offset)
        return [l.rstrip("\n") for l in lines if l.strip()]
```

**Padrão crítico herdado:** `encoding="utf-8", errors="replace"` — nomes de documentos Windows com caracteres especiais não podem crashar o watcher (Pitfall do RESEARCH.md).

---

### `backend/app/services/retention.py` (service, batch)

**Análogo:** Nenhum no codebase. Padrão de RESEARCH.md §Padrão + §Don't Hand-Roll.

**Padrão de purge com thread daemon** (RESEARCH.md linhas 572–579):
```python
import time
import threading
from datetime import datetime, timedelta, timezone
from sqlalchemy import delete
from app.models.print_job import PrintJob

def purge_old_jobs(session, retention_days: int) -> int:
    """Retorna número de registros deletados."""
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=retention_days)
    result = session.execute(
        delete(PrintJob).where(PrintJob.timestamp < cutoff)
    )
    session.commit()
    return result.rowcount

def start_retention_loop(session_factory, retention_days: int) -> threading.Thread:
    """Thread daemon para purge horário (DATA-01)."""
    def _loop():
        while True:
            with session_factory() as session:
                purge_old_jobs(session, retention_days)
            time.sleep(3600)   # 1h entre purges
    t = threading.Thread(target=_loop, daemon=True, name="retention-loop")
    t.start()
    return t
```

**Padrão estabelecido (RESEARCH.md §Don't Hand-Roll):** thread daemon + `time.sleep(3600)` em vez de APScheduler (overhead) ou cron do host OS (não existe no container).

---

### `scripts/validate-phase2.sh` (utility)

**Análogo:** `scripts/validate-phase1.sh` — **match exato de estrutura**

**Padrão estabelecido** (`validate-phase1.sh` linhas 1–8, 14–27, 317–368):
```bash
#!/usr/bin/env bash
# PrintWatch — validação Fase N
# Uso: bash scripts/validate-phaseN.sh [--quick]

set -euo pipefail

# Git Bash/MSYS: evita conversão de paths Windows
if [[ -n "${MSYSTEM:-}" ]] || [[ "$(uname -s 2>/dev/null)" == MINGW* ]]; then
  export MSYS_NO_PATHCONV=1
fi

QUICK_MODE=false
STRICT_RUNTIME=false
FAILURES=0
WARNINGS=0

pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; FAILURES=$((FAILURES + 1)); }
warn() { echo "[WARN] $1"; WARNINGS=$((WARNINGS + 1)); }

check_file_exists() {
  local path="$1"
  local required="$2"
  if [[ -f "$path" ]]; then
    pass "Arquivo presente: $path"
  elif [[ "$required" == "required" ]]; then
    fail "Arquivo ausente (obrigatório): $path"
  else
    warn "Arquivo ausente (esperado em plano futuro): $path"
  fi
}

run_quick() {
  echo "=== PrintWatch validate-phase2 (--quick) ==="
  STRICT_RUNTIME=false
  check_file_exists "backend/Dockerfile" "required"
  check_file_exists "backend/requirements.txt" "required"
  check_file_exists "backend/app/main.py" "required"
  # ... outros checks de arquivos e runtime
  echo "=== Resumo: ${FAILURES} FAIL, ${WARNINGS} WARN ==="
  [[ "$FAILURES" -gt 0 ]] && exit 1; exit 0
}
```

**Checks específicos da Fase 2 a adicionar:**
- `docker compose ps backend` → container running
- `docker compose exec -T backend stat -c '%a' /app/data/printwatch.db` → permissões `600` (DATA-03)
- `docker compose exec -T backend python -c "from app.services.parser import parse_page_log_line; ..."` → parser importa
- `docker compose exec -T backend sqlite3 /app/data/printwatch.db ".tables"` → tabelas criadas
- Contagem de registros após job de teste (CAPTURE-02: ≤ 30s)

---

### `docker-compose.yml` (modificar)

**Análogo:** `docker-compose.yml` atual — **match exato**

**Padrão existente** (`docker-compose.yml` linhas 1–25):
```yaml
# D-01/D-02: backend, frontend e nginx entram nas Fases 2–4 — sem stubs ativos (D-03).

services:
  cups:
    build: ./cups
    ports:
      - "631:631"
    env_file: .env
    environment:
      ALLOWED_NETWORK: ${ALLOWED_NETWORK:-REDACTED_IP/16}
    volumes:
      - cups_logs:/var/log/cups
      - cups_spool:/var/spool/cups
    restart: unless-stopped

volumes:
  cups_logs:
  cups_spool:
```

**Bloco a adicionar (padrão de expansão por fase sem stubs — D-03 Fase 1):**
```yaml
  backend:
    build: ./backend
    env_file: .env
    environment:
      DB_PATH: /app/data/printwatch.db
      LOG_PATH: /var/log/cups/page_log
      LOG_RETENTION_DAYS: ${LOG_RETENTION_DAYS:-90}
    volumes:
      - cups_logs:/var/log/cups:ro     # D-17: read-only — CUPS não depende do backend
      - db_data:/app/data
    restart: unless-stopped
    depends_on:
      - cups

volumes:
  cups_logs:
  cups_spool:
  db_data:    # DATA-02: persistência do SQLite
```

**Padrão crítico herdado:** `restart: unless-stopped` e comentários de fase (D-03 da Fase 1) — manter estilo de comentários para identificação de expansão por fase.

---

### `.env.example` (modificar)

**Análogo:** `.env.example` atual — **match exato**

**Padrão existente** (`.env.example` linhas 1–23):
```bash
# PrintWatch — variáveis de ambiente (Fase 1)
#
# Copie este arquivo para .env antes de executar `docker compose up -d`:
#   cp .env.example .env
#
# IMPORTANTE: Nunca commite o arquivo .env — ele contém credenciais reais (D-19).
# Este arquivo usa apenas placeholders seguros para documentação.

ALLOWED_NETWORK=REDACTED_IP/16
CUPS_ADMIN_USER=admin
CUPS_ADMIN_PASSWORD=changeme
TEST_PRINTER_NAME=test_printer
```

**Linhas a adicionar (manter estilo de comentários com referência a decisões):**
```bash
# Fase 2 — backend log pipeline (D-16)
LOG_RETENTION_DAYS=90
DB_PATH=/app/data/printwatch.db
LOG_PATH=/var/log/cups/page_log
```

---

## Shared Patterns (Padrões Transversais)

### Padrão 1: Entrypoint com `set -euo pipefail` + `exec`

**Fonte:** `cups/entrypoint.sh` linhas 1–2, 28
**Aplicar a:** `backend/entrypoint.sh`

```bash
#!/bin/bash
set -euo pipefail
# ... configuração ...
exec <processo-principal>
```

`set -euo pipefail` garante que qualquer erro (variável undefined, comando falho, pipe) aborta o script imediatamente. `exec` substitui o shell pelo processo principal → PID 1 correto para sinais Docker.

---

### Padrão 2: Funções de output pass/fail/warn

**Fonte:** `scripts/validate-phase1.sh` linhas 24–26; `scripts/bootstrap-vm.sh` linhas 15–17
**Aplicar a:** `scripts/validate-phase2.sh`

```bash
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; FAILURES=$((FAILURES + 1)); }
warn() { echo "[WARN] $1"; WARNINGS=$((WARNINGS + 1)); }
```

Padrão estabelecido nos scripts bash do projeto. Mantém output consistente e contagem de falhas.

---

### Padrão 3: MSYS_NO_PATHCONV guard

**Fonte:** `scripts/validate-phase1.sh` linhas 10–12
**Aplicar a:** `scripts/validate-phase2.sh`

```bash
if [[ -n "${MSYSTEM:-}" ]] || [[ "$(uname -s 2>/dev/null)" == MINGW* ]]; then
  export MSYS_NO_PATHCONV=1
fi
```

Git Bash/MSYS converte paths como `/var/log/...` para paths Windows automaticamente. Este guard previne o problema em `docker compose exec` com paths Unix.

---

### Padrão 4: Variáveis de ambiente com defaults

**Fonte:** `cups/entrypoint.sh` linhas 4–6; `docker-compose.yml` linha 11
**Aplicar a:** `backend/entrypoint.sh`, `backend/app/core/config.py`

```bash
# Shell
VARIAVEL="${VARIAVEL:-valor_default}"
```

```yaml
# Docker Compose
environment:
  VARIAVEL: ${VARIAVEL:-valor_default}
```

Padrão consistente nos dois tiers (compose + entrypoint). Garante que o container sobe com defaults razoáveis sem `.env` obrigatório.

---

### Padrão 5: SQLAlchemy `Optional[T]` para campos nullable (D-09)

**Fonte:** `02-RESEARCH.md` §Padrão 3 (linhas 354–358)
**Aplicar a:** `backend/app/models/print_job.py`

```python
color_mode: Mapped[Optional[str]] = mapped_column(String(50))   # NULL se '-' no CUPS
host_origin: Mapped[Optional[str]] = mapped_column(String(255)) # NULL se '-' no CUPS
```

`Optional[T]` no tipo Python se traduz automaticamente em coluna nullable no SQLAlchemy 2.x. Nunca usar `default=""` ou `default="unknown"`.

---

### Padrão 6: `NULL` semântico via `_null_if_dash()`

**Fonte:** `scripts/validate-phase1.sh` linha 20 (sentinel `-` identificado na amostra)
**Aplicar a:** `backend/app/services/parser.py`

```python
def _null_if_dash(value: str) -> Optional[str]:
    return None if value.strip() == "-" else value.strip()
```

O CUPS usa `-` como sentinel para campos ausentes no `page_log`. Converter para `None` Python → `NULL` SQL é o único ponto onde o mapeamento acontece.

---

## No Analog Found

Arquivos sem análogo próximo no codebase — planner deve usar padrões do RESEARCH.md:

| Arquivo | Role | Data Flow | Motivo |
|---------|------|-----------|--------|
| `backend/requirements.txt` | config | — | Primeiro arquivo Python do projeto |
| `backend/app/main.py` | provider | request-response | Sem FastAPI/Python no repo ainda |
| `backend/app/core/database.py` | config | — | Sem ORM/SQLAlchemy no repo ainda |
| `backend/app/models/print_job.py` | model | CRUD | Sem modelos ORM no repo ainda |
| `backend/app/models/capture_state.py` | model | CRUD | Sem modelos ORM no repo ainda |
| `backend/app/models/policy.py` | model | CRUD | Sem modelos ORM no repo ainda |
| `backend/app/repositories/print_job_repo.py` | service | CRUD | Sem repository pattern no repo ainda |
| `backend/app/services/log_watcher.py` | service | event-driven | Sem watchdog/event-driven no repo ainda |
| `backend/app/services/tail_reader.py` | service | file-I/O | Sem file-tailing no repo ainda |
| `backend/app/services/retention.py` | service | batch | Sem batch jobs Python no repo ainda |

**Fonte para estes arquivos:** `02-RESEARCH.md` §Padrões 1–4 (todos verificados via Context7 + PyPI registry).

---

## Metadata

**Escopo de busca de análogos:** `d:\Programação\printwatch\` (recursivo)
**Arquivos Python encontrados:** 0 (Fase 2 introduz o primeiro módulo Python)
**Arquivos Dockerfile encontrados:** 1 (`cups/Dockerfile`)
**Arquivos shell encontrados:** 5 (`validate-phase1.sh`, `entrypoint.sh`, `bootstrap-vm.sh`, `setup-printer.sh`, `verify-vm-network.sh`)
**Data do mapeamento:** 2026-05-26
