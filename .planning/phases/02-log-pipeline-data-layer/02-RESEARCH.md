# Phase 2: Log Pipeline & Data Layer - Research

**Pesquisado:** 2026-05-26  
**Domínio:** Pipeline de captura de logs CUPS → SQLite (Python watchdog + SQLAlchemy 2.x + FastAPI)  
**Confiança:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Granularidade no banco**
- **D-01:** Persistir uma linha por página no SQLite — espelhamento 1:1 com cada linha do `page_log` do CUPS.
- **D-02:** Não agregar por job na ingestão; agregação fica para a camada de leitura (Fase 3/4) via query ou view.
- **D-03:** Parser permanece simples — mapear linha → registro, sem lógica de rollup.

**Checkpoint do watcher (CAPTURE-03)**
- **D-04:** Persistir inode + byte offset do `page_log` em tabela `capture_state` no SQLite.
- **D-05:** Em restart: mesmo inode → `seek(offset)` e continuar tail; inode diferente → reprocessar do início do novo arquivo.
- **D-06:** Não usar hash de linha nem scan completo do histórico na subida.
- **D-07:** Estratégia deve ser compatível com logrotate futuro.

**Normalização de campos**
- **D-08:** Username mantido exatamente como recebido do CUPS — ex.: `DOMAIN\usuario`.
- **D-09:** Campos ausentes → NULL no banco; nunca string vazia, nunca placeholder `"unknown"`.
- **D-10:** Diferenciar semanticamente "campo inexistente na origem" de "valor conhecido".

**Escopo do container backend (Fase 2)**
- **D-11:** Único container `backend` com estrutura FastAPI (arquitetura definitiva), montando `cups_logs:ro` e volume `db_data`.
- **D-12:** Sem rotas REST, autenticação ou Swagger nesta fase.
- **D-13:** Componentes ativos: watcher, parser, SQLite, repository/service, healthcheck interno simples.
- **D-14:** Objetivo: `page_log → watcher → parser → SQLite` automático e resiliente.

**Requisitos herdados**
- **D-15:** `print_jobs.status` default `allowed`; tabela `policies` vazia; hook `pre_process_job` retorna `True`.
- **D-16:** Retenção configurável via `LOG_RETENTION_DAYS`; volumes Docker persistentes; SQLite permissões `600`.
- **D-17:** CUPS independente se backend/watcher cair; watcher monta `page_log` read-only.

### Claude's Discretion
- Schema exato de colunas em `print_jobs` (além dos campos CAPTURE-01, mapeados do PAGE_LOG_REGEX).
- Idempotência ao reprocessar arquivo novo (inode mudou) — constraint única composta.
- Mecanismo de purge por `LOG_RETENTION_DAYS` (startup, cron interno, ou ambos).
- Layout de pacotes Python (`backend/app/`, etc.) e process manager do watcher (thread, asyncio task, ou subprocess).
- Formato do healthcheck interno (arquivo, socket, ou comando).
- Script `validate-phase2.sh` espelhando padrão da Fase 1.

### Deferred Ideas (OUT OF SCOPE)
- Agregação por job na ingestão — rejeitada; usar queries/views nas Fases 3–4.
- API REST / Swagger / auth — Fase 3+.
- Dashboard e nginx — Fases 4–5.
- Políticas de bloqueio ativas — Fase 2+ (hook existe, sempre `allowed` no MVP).
- Hash de linha ou scan completo para checkpoint — explicitamente rejeitados.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Descrição | Suporte da Pesquisa |
|----|-----------|---------------------|
| CAPTURE-01 | Registrar cada job com: timestamp, username (DOMINIO\usuario), printer, job_name, pages, copies, media, sides, color_mode, host_origin | PAGE_LOG_REGEX mapeado em §Code Examples; schema SQLAlchemy com Optional[str] para campos nullable |
| CAPTURE-02 | Job aparece no banco em ≤ 30 segundos após impressão | watchdog InotifyObserver (Linux) detecta `on_modified` em ms; overhead de parse + INSERT SQLite < 1s |
| CAPTURE-03 | Restart não duplica nem perde registros | Checkpoint inode+offset em `capture_state`; seek(offset) no mesmo inode; UNIQUE constraint para idempotência |
| CAPTURE-04 | CUPS funciona se backend cair | Volume `cups_logs` montado `:ro`; CUPS escreve diretamente, não depende do backend |
| DATA-01 | Retenção configurável via `LOG_RETENTION_DAYS` | DELETE WHERE timestamp < NOW() - INTERVAL; executar no startup e como cron interno |
| DATA-02 | Volumes Docker garantem persistência | Volume `db_data` em docker-compose; SQLite em path fixo dentro do volume |
| DATA-03 | SQLite com permissões 600 | `chmod 600` no entrypoint antes de iniciar o watcher |
| EXTEND-01 | Coluna `status` com default `allowed` | `mapped_column(String, default="allowed")` no modelo SQLAlchemy |
| EXTEND-02 | Tabela `policies` criada vazia | Modelo `Policy` com `Base.metadata.create_all()` |
| EXTEND-03 | Hook `pre_process_job(job_data)` retorna `True` no MVP | Função stub no módulo de serviço |
</phase_requirements>

---

## Summary

A Fase 2 constrói o pipeline de captura: o CUPS já está operacional (Fase 1) escrevendo em `/var/log/cups/page_log`. O objetivo é um processo Python que monitora esse arquivo em tempo real, parseia cada nova linha com o `PAGE_LOG_REGEX` validado na Fase 1 e persiste um registro por página no SQLite.

O stack é todo validado em produção: **watchdog 6.0.0** usa `InotifyObserver` no Linux (Docker Ubuntu), que detecta modificações de arquivo via `inotify` do kernel em milissegundos — sem polling. O watcher agendará o diretório pai `/var/log/cups/` e filtrará eventos pelo path `page_log`. O loop de leitura usa `seek()` para continuar da última posição, e um mecanismo de comparação de inode (`os.stat(...).st_ino`) trata logrotate. **SQLAlchemy 2.0.50** com a nova API `Mapped`/`mapped_column` e `DeclarativeBase` é o padrão atual; a connection string SQLite usa 4 barras para path absoluto e `check_same_thread=False` (necessário com watcher em thread separada). A idempotência no reprocessamento (inode mudou) é resolvida com `UNIQUE` composta + `INSERT ... ON CONFLICT DO NOTHING` da API SQLite-dialect do SQLAlchemy.

**Recomendação primária:** Watcher como thread daemon (não subprocess), SQLAlchemy Session com `sessionmaker` + `NullPool` (evita lock no SQLite file-based), volume Docker `db_data` mapeado para `/app/data/printwatch.db`.

---

## Architectural Responsibility Map

| Capacidade | Tier Primário | Tier Secundário | Justificativa |
|------------|---------------|-----------------|---------------|
| Detecção de novas linhas no page_log | Backend / Processo Python | — | watchdog com InotifyObserver lê eventos de kernel; roda dentro do container `backend` |
| Parse de linha → dict de campos | Backend / Parser Python | — | Regex em Python puro; lógica de domínio pertence ao backend |
| Checkpoint inode + offset | Database / SQLite | Backend (leitura/escrita) | Estado persistente deve sobreviver a restart; tabela `capture_state` |
| Persistência dos jobs | Database / SQLite | — | SQLAlchemy ORM; volume `db_data` garante persistência |
| Purge por retenção | Backend / Service | — | Job no startup + loop periódico interno; sem dependência de cron do OS host |
| Hook `pre_process_job` | Backend / Service | — | Ponto de extensão na camada de serviço; sem tier externo no MVP |
| Healthcheck interno | Backend / Processo | — | Verificação de processo/dependências; sem endpoint público (D-12) |
| Volume read-only do CUPS | Infraestrutura / Docker | — | `cups_logs:ro` — CUPS escreve, backend só lê; independência garantida (D-17) |

---

## Standard Stack

### Core

| Biblioteca | Versão | Propósito | Por que padrão |
|------------|--------|-----------|----------------|
| watchdog | 6.0.0 | Monitor de filesystem, detecta modificações no page_log | Padrão da indústria para file-watching em Python; InotifyObserver usa syscall inotify do Linux (zero polling) [VERIFIED: PyPI registry] |
| SQLAlchemy | 2.0.50 | ORM + gerenciamento de sessão para SQLite | API `Mapped`/`mapped_column` é a interface definitiva 2.x; 18.000+ snippets de docs oficiais [VERIFIED: PyPI registry] |
| FastAPI | 0.136.3 | Esqueleto do container backend (rotas virão na Fase 3) | Stack definido em PROJECT.md; async nativo, Pydantic 2 integrado [VERIFIED: PyPI registry] |
| uvicorn | 0.48.0 | ASGI server (necessário mesmo que sem rotas públicas) | Padrão para FastAPI; necessário para o processo principal do container [VERIFIED: PyPI registry] |
| pydantic | 2.13.4 | Validação de dados (FastAPI usa automaticamente) | Instalado como dependência do FastAPI 0.136.x [VERIFIED: PyPI registry] |

### Supporting

| Biblioteca | Versão | Propósito | Quando usar |
|------------|--------|-----------|-------------|
| alembic | 1.18.4 | Migrações de schema SQLite | Não obrigatório no MVP (schema criado via `create_all`), mas adicionar para extensibilidade das Fases 3–5 |
| python-dotenv | — | Carregar variáveis do `.env` no container | Alternativa: usar `env_file` no compose e ler via `os.environ` — mais simples no MVP |

### Alternativas Consideradas

| Em vez de | Poderia Usar | Trade-off |
|-----------|-------------|-----------|
| watchdog InotifyObserver | PollingObserver | Polling funciona em qualquer FS/CIFS, mas adiciona latência e CPU; InotifyObserver é correto para Linux Docker |
| watchdog | pyinotify diretamente | pyinotify é Linux-only e mais baixo nível; watchdog abstrai a API e adiciona reconexão automática |
| SQLAlchemy ORM | sqlite3 puro | sqlite3 funciona, mas SQLAlchemy provê session management, `UNIQUE` constraint handling, e será necessário para as Fases 3–5 (queries complexas, filtros) |
| thread daemon | asyncio task | asyncio seria correto para FastAPI, mas watchdog Observer roda em thread própria; misturar asyncio + blocking file I/O exige `run_in_executor` — thread separada é mais simples e correta aqui |

**Instalação:**
```bash
pip install watchdog==6.0.0 "sqlalchemy==2.0.50" "fastapi==0.136.3" "uvicorn[standard]==0.48.0" "pydantic==2.13.4"
```

---

## Package Legitimacy Audit

> Protocolo executado via `pip index versions` (PyPI) em 2026-05-26 no ambiente local.

| Pacote | Registry | Idade | Uso | Source Repo | Verificação | Disposição |
|--------|----------|-------|-----|-------------|-------------|------------|
| watchdog | PyPI | ~14 anos | Ubíquo em projetos Python de file-watching | github.com/gorakhargosh/watchdog | OK — 6.0.0 confirmado via `pip index` | Aprovado |
| sqlalchemy | PyPI | ~18 anos | Referência ORM para Python | github.com/sqlalchemy/sqlalchemy | OK — 2.0.50 confirmado via `pip index` | Aprovado |
| fastapi | PyPI | ~6 anos | Framework web moderno de alta adoção | github.com/tiangolo/fastapi | OK — 0.136.3 confirmado via `pip index` | Aprovado |
| uvicorn | PyPI | ~7 anos | ASGI server padrão do FastAPI | github.com/encode/uvicorn | OK — 0.48.0 confirmado via `pip index` | Aprovado |
| pydantic | PyPI | ~8 anos | Validação de dados; dependência transitiva do FastAPI | github.com/pydantic/pydantic | OK — 2.13.4 confirmado via `pip index` | Aprovado |
| alembic | PyPI | ~13 anos | Migrações; opcional no MVP | github.com/sqlalchemy/alembic | OK — 1.18.4 confirmado via `pip index` | Aprovado (opcional) |

**Pacotes removidos por slopcheck [SLOP]:** nenhum  
**Pacotes flagged como suspeitos [SUS]:** nenhum  

*slopcheck não está instalado no ambiente. Verificação alternativa via `pip index versions` (PyPI oficial) + reputação de source repo conhecida. Todos os pacotes têm anos de histórico e milhões de downloads semanais.*

---

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  Volume: cups_logs (shared, read-only para backend)             │
│                                                                  │
│  Container CUPS          Container backend                       │
│  ┌──────────────┐        ┌────────────────────────────────────┐ │
│  │              │        │                                    │ │
│  │  CUPS print  │        │  watchdog InotifyObserver          │ │
│  │  server      │        │  ├─ schedules /var/log/cups/       │ │
│  │              │        │  └─ on_modified(page_log)          │ │
│  │  page_log ──►│──:ro──►│       │                            │ │
│  │  (append)    │        │       ▼                            │ │
│  │              │        │  TailReader                        │ │
│  └──────────────┘        │  ├─ seek(offset) se mesmo inode   │ │
│                           │  ├─ reopen do início se inode ≠   │ │
│                           │  └─ readlines() → linhas novas    │ │
│                           │       │                            │ │
│                           │       ▼                            │ │
│                           │  PageLogParser                     │ │
│                           │  └─ re.match(PAGE_LOG_REGEX, line)│ │
│                           │       │ campos → dict/None         │ │
│                           │       ▼                            │ │
│                           │  pre_process_job(job) → True (MVP)│ │
│                           │       │                            │ │
│                           │       ▼                            │ │
│                           │  PrintJobRepository                │ │
│                           │  ├─ INSERT OR IGNORE (UNIQUE)     │ │
│                           │  └─ UPDATE capture_state          │ │
│                           │       │                            │ │
│                           │       ▼                            │ │
│                           │  SQLite DB  ◄── Volume: db_data   │ │
│                           │  ├─ print_jobs                    │ │
│                           │  ├─ capture_state                 │ │
│                           │  └─ policies (vazia)              │ │
│                           │                                    │ │
│                           │  FastAPI app (sem rotas — Fase 3) │ │
│                           │  └─ uvicorn (porta interna)       │ │
│                           └────────────────────────────────────┘ │
│                                                                  │
│  Volume: db_data (persistente, chmod 600)                        │
└─────────────────────────────────────────────────────────────────┘
```

### Estrutura de Pacotes Python Recomendada

```
backend/
├── Dockerfile
├── requirements.txt
├── entrypoint.sh          # chmod 600 db + start uvicorn/watcher
└── app/
    ├── __init__.py
    ├── main.py            # FastAPI app instance (sem rotas na fase 2)
    ├── core/
    │   ├── config.py      # settings via env vars (LOG_RETENTION_DAYS, DB_PATH, LOG_PATH)
    │   └── database.py    # create_engine, sessionmaker, Base
    ├── models/
    │   ├── __init__.py
    │   ├── print_job.py   # PrintJob (ORM model)
    │   ├── policy.py      # Policy (ORM model, vazio no MVP)
    │   └── capture_state.py  # CaptureState (inode + offset)
    ├── repositories/
    │   ├── __init__.py
    │   └── print_job_repo.py  # insert_job(), get_capture_state(), update_capture_state()
    ├── services/
    │   ├── __init__.py
    │   ├── log_watcher.py  # LogWatcher(FileSystemEventHandler), Observer lifecycle
    │   ├── tail_reader.py  # TailReader: seek/inode-check/readlines
    │   ├── parser.py       # PageLogParser: regex → dict, NULL para campos ausentes
    │   └── retention.py   # purge_old_jobs(days)
    └── scripts/
        └── validate-phase2.sh  # Validação Nyquist espelhando Fase 1
```

### Padrão 1: Watcher com InotifyObserver (Linux)

**O quê:** Usar `InotifyObserver` explicitamente no Linux Docker para receber eventos do kernel sem polling.  
**Quando usar:** Sempre no container backend (Ubuntu Linux).

```python
# Source: https://context7.com/gorakhargosh/watchdog/llms.txt
import time
from watchdog.observers.inotify import InotifyObserver
from watchdog.events import FileSystemEventHandler, FileModifiedEvent

class PageLogHandler(FileSystemEventHandler):
    PAGE_LOG_PATH = "/var/log/cups/page_log"

    def __init__(self, tail_reader, processor):
        self._tail = tail_reader
        self._processor = processor

    def on_modified(self, event):
        if not event.is_directory and event.src_path == self.PAGE_LOG_PATH:
            for line in self._tail.read_new_lines():
                self._processor.process(line)

observer = InotifyObserver()
handler = PageLogHandler(tail_reader, processor)
# Observa o DIRETÓRIO pai — watchdog monitora dirs, não arquivos individuais
observer.schedule(handler, path="/var/log/cups", recursive=False)
observer.start()
try:
    while True:
        time.sleep(1)
finally:
    observer.stop()
    observer.join()
```

> **Importante:** `observer.schedule()` recebe um **diretório**, não um arquivo. O handler filtra pelo path `page_log` no método `on_modified`.

### Padrão 2: TailReader com Checkpoint Inode + Offset (D-04, D-05)

**O quê:** Lê novas linhas a partir do `seek(offset)` salvo; detecta logrotate via mudança de inode.  
**Quando usar:** Em todo ciclo de leitura disparado pelo `on_modified`.

```python
# Source: StackOverflow verified pattern + Python stdlib os.stat docs
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
        """No startup: carrega inode+offset do banco (D-05)."""
        state = self._state_repo.get()
        current_stat = os.stat(self.path)
        current_inode = current_stat.st_ino

        if state and state.inode == current_inode:
            # Mesmo inode → seek para offset salvo
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
        """Chamado pelo on_modified; retorna novas linhas e atualiza checkpoint."""
        current_inode = os.stat(self.path).st_ino

        if current_inode != self._inode:
            # Logrotate: arquivo novo criado em mesmo path
            self._fh.close()
            self._inode = current_inode
            self._offset = 0
            self._fh = open(self.path, "r", encoding="utf-8", errors="replace")

        lines = self._fh.readlines()
        if lines:
            self._offset = self._fh.tell()
            self._state_repo.upsert(inode=self._inode, byte_offset=self._offset)
        return [l.rstrip("\n") for l in lines if l.strip()]
```

### Padrão 3: SQLAlchemy 2.x com DeclarativeBase + Mapped (ORM moderno)

**O quê:** Definição de modelo com anotações de tipo, engine SQLite com `NullPool` para evitar lock em file-based DB com múltiplas threads.  
**Quando usar:** Padrão SQLAlchemy 2.x — não usar `Column()` legado.

```python
# Source: https://docs.sqlalchemy.org/en/20/orm/quickstart.html
from sqlalchemy import create_engine, UniqueConstraint, String, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.pool import NullPool
from typing import Optional
from datetime import datetime

class Base(DeclarativeBase):
    pass

class PrintJob(Base):
    __tablename__ = "print_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Campos diretos do page_log (CAPTURE-01)
    printer: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)   # D-08: sem strip de domínio
    job_id: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    pages: Mapped[int] = mapped_column(Integer, nullable=False)
    color_mode: Mapped[Optional[str]] = mapped_column(String(50))         # D-09: NULL se ausente
    host_origin: Mapped[Optional[str]] = mapped_column(String(255))       # D-09: NULL se ausente
    job_name: Mapped[Optional[str]] = mapped_column(String(512))
    media: Mapped[Optional[str]] = mapped_column(String(100))
    sides: Mapped[Optional[str]] = mapped_column(String(50))
    copies: Mapped[Optional[int]] = mapped_column(Integer)
    # Extensibilidade (D-15, EXTEND-01)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="allowed")
    # Idempotência para reprocessamento (Claude's Discretion)
    __table_args__ = (
        UniqueConstraint("printer", "job_id", "timestamp", "pages", name="uq_page_log_line"),
    )

class CaptureState(Base):
    __tablename__ = "capture_state"
    id: Mapped[int] = mapped_column(primary_key=True)
    log_path: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    inode: Mapped[int] = mapped_column(Integer, nullable=False)
    byte_offset: Mapped[int] = mapped_column(Integer, nullable=False)

class Policy(Base):
    __tablename__ = "policies"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # Vazia no MVP (EXTEND-02) — colunas definidas nas Fases 2+

# Engine: NullPool previne locking issues em SQLite file-based com threads
engine = create_engine(
    "sqlite:////app/data/printwatch.db",
    connect_args={"check_same_thread": False},
    poolclass=NullPool,
)
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(engine)
```

### Padrão 4: INSERT OR IGNORE via Dialeto SQLite (Idempotência)

**O quê:** Ao reprocessar arquivo com inode novo, evitar duplicatas usando `ON CONFLICT DO NOTHING`.  
**Quando usar:** Em todo INSERT de `print_jobs` — torna a operação idempotente sem hash de linha (D-06).

```python
# Source: https://docs.sqlalchemy.org/en/20/dialects/sqlite.html
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

def insert_job_idempotent(session, job_dict: dict):
    stmt = sqlite_insert(PrintJob).values(**job_dict)
    stmt = stmt.on_conflict_do_nothing(
        index_elements=["printer", "job_id", "timestamp", "pages"]
    )
    session.execute(stmt)
    session.commit()
```

### Anti-Padrões a Evitar

- **Monitorar o arquivo diretamente com watchdog:** `observer.schedule()` recebe diretório. Monitorar `/var/log/cups/page_log` como path gera erro silencioso — sempre agendar `/var/log/cups/` e filtrar no handler.
- **Column() legado do SQLAlchemy 1.x:** Usar `Mapped[T] = mapped_column(...)` em vez de `Column(String)` — a nova API é type-safe e o padrão oficial 2.x.
- **StaticPool com arquivo SQLite:** Para SQLite em arquivo (não `:memory:`), usar `NullPool` em vez de `StaticPool` para evitar file locking entre threads.
- **Guardar file handle sem verificar inode:** Após cada leitura, verificar se `os.stat(path).st_ino == self._inode` antes do próximo `readlines()` — não confiar no evento watchdog para detectar rotação.
- **open() com encoding default:** Usar `encoding="utf-8", errors="replace"` — nomes de documentos de usuários Windows podem conter caracteres especiais.
- **Watcher rodando como root no container:** Não necessário; o watcher só precisa de permissão de leitura no volume `:ro`.

---

## Don't Hand-Roll

| Problema | Não construir | Usar em vez | Motivo |
|----------|--------------|-------------|--------|
| Detecção de eventos de filesystem | Loop `while True: os.stat()` | watchdog InotifyObserver | O polling custom consome CPU e tem latência variável; InotifyObserver é O(1) via syscall do kernel |
| Deduplicação de linhas | Hash SHA256 de cada linha | `UNIQUE` constraint + `ON CONFLICT DO NOTHING` | Hash é custoso e aumenta footprint; constraint na chave natural é mais simples, indexada e sem coluna extra |
| Migrações de schema | Scripts SQL manuais | Alembic (opcional MVP) + `create_all()` | `create_all()` é suficiente no MVP; Alembic estará disponível nas Fases 3–5 sem refactor |
| Parse de timestamp CUPS | `strptime` custom | `datetime.strptime(ts, "%d/%b/%Y:%H:%M:%S %z")` | O formato do CUPS é fixo (`[26/May/2026:14:30:00 +0000]`); usar strptime com format string, não regex separado |
| Purge periódico | cron externo no host | Thread daemon interna + loop `time.sleep(3600)` | Cron host não existe no container; APScheduler é overhead desnecessário para 1 tarefa horária |

**Insight chave:** O SQLite file-based com `NullPool` e `check_same_thread=False` é a configuração correta para uso com watcher em thread separada. O padrão oposto (`QueuePool` default) causa `OperationalError: database is locked` em cenários de alta frequência de escrita.

---

## Mapeamento PAGE_LOG_REGEX → Colunas SQLAlchemy

O `PAGE_LOG_REGEX` da Fase 1 (`scripts/validate-phase1.sh` linha 20):

```
^(\S+)\s+(\S+)\s+(\d+)\s+\[(.+?)\]\s+total\s+(\d+)\s+(\S+)\s+(\S+)\s+(.+?)\s+(\S+)\s+(\S+)$
```

E o `PageLogFormat` do `cupsd.conf.template`:
```
PageLogFormat "%p %u %j %T %P %C %{job-billing} %{job-originating-host-name} %{job-name} %{media} %{sides}"
```

| Grupo Regex | Campo CUPS | Coluna SQLAlchemy | Tipo | Nullable | Notas |
|-------------|-----------|-------------------|------|----------|-------|
| `\1` (group 1) | `%p` printer | `printer` | `String(255)` | NOT NULL | Nome da impressora |
| `\2` (group 2) | `%u` username | `username` | `String(255)` | NOT NULL | D-08: manter `DOMINIO\usuario` |
| `\3` (group 3) | `%j` job-id | `job_id` | `Integer` | NOT NULL | ID numérico do job |
| `\4` (group 4) | `%T` timestamp | `timestamp` | `DateTime` | NOT NULL | Parse: `[DD/Mon/YYYY:HH:MM:SS +ZZZZ]` |
| `\5` (group 5) | `%P` pages | `pages` | `Integer` | NOT NULL | Total de páginas |
| `\6` (group 6) | `%C` color (billing) | `color_mode` | `String(50)` | NULL | D-09: `-` = NULL; HP/Samsung pode omitir |
| `\7` (group 7) | `%{job-billing}` | *mapeado em color_mode ou billing* | — | — | Verificar se CUPS separa `%C` de `%{job-billing}` |
| `\8` (group 8) | `%{job-originating-host-name}` | `host_origin` | `String(255)` | NULL | D-09: IP ou hostname do cliente Windows |
| `\9` (group 9) | `%{job-name}` | `job_name` | `String(512)` | NULL | Nome do documento |
| `\10` (group 10) | `%{media}` | `media` | `String(100)` | NULL | ex.: `na_iso_a4_210x297mm` |
| `\11` (group 11) | `%{sides}` | `sides` | `String(50)` | NULL | ex.: `one-sided`, `two-sided-long-edge` |

> **Nota:** O regex tem 10 grupos de captura. O `PageLogFormat` mostra 11 campos (`%p %u %j %T %P %C %{job-billing} ...`). A linha de amostra em `validate-phase1.sh` (linha 276) é:
> `test_printer DOMINIO\usuario 42 [26/May/2026:14:30:00 +0000] total 3 - 192.168.1.10 relatorio.pdf na_iso_a4_210x297mm one-sided`
> 
> Nessa amostra: grupo 6 = `-` (color/billing ausente), grupo 7 = `192.168.1.10` (host_origin). O campo `copies` **não aparece** no `PageLogFormat` atual — será derivado do contexto do job ou ficará NULL. Esta é uma área de **Claude's Discretion** para confirmar na implementação.

**Regra de NULL (D-09):** No parser, converter `-` (valor sentinel do CUPS para campo vazio) para `None` → `NULL` no banco.

---

## Common Pitfalls

### Pitfall 1: Watchdog monitora diretórios, não arquivos
**O que dá errado:** Chamar `observer.schedule(handler, path="/var/log/cups/page_log")` — o watchdog ignora silenciosamente ou lança erro.  
**Por que acontece:** A API do watchdog é projetada para diretórios; eventos de arquivo são filtrados pelo handler.  
**Como evitar:** Sempre agendar o **diretório pai** (`/var/log/cups/`); no `on_modified`, verificar `event.src_path == "/var/log/cups/page_log"`.  
**Sinal de alerta:** Nenhum evento disparado mesmo com novos jobs no page_log.

### Pitfall 2: SQLite locking com múltiplas threads (QueuePool default)
**O que dá errado:** `OperationalError: database is locked` intermitente quando watcher thread e FastAPI thread fazem writes simultâneos.  
**Por que acontece:** O `QueuePool` default do SQLAlchemy mantém conexões abertas em cache; SQLite file-based não suporta múltiplos writers simultâneos.  
**Como evitar:** `create_engine(..., poolclass=NullPool)` + `check_same_thread=False`; cada operação abre e fecha sua própria conexão.  
**Sinal de alerta:** Erros de lock esporádicos sob carga ou durante testes com threads.

### Pitfall 3: Perda de linhas no restart sem seek correto
**O que dá errado:** Reiniciar o watcher sem `seek(offset)` faz reprocessar o arquivo inteiro (duplicatas) ou pular linhas (se file pointer no fim).  
**Por que acontece:** File handles não persistem entre processos.  
**Como evitar:** D-05 implementado com `capture_state`; no startup, **sempre** ler inode + offset do banco antes de abrir o arquivo.  
**Sinal de alerta:** Duplicatas no banco após restart, ou gaps de jobs em períodos de downtime.

### Pitfall 4: Logrotate sem detecção de inode
**O que dá errado:** Watcher continua lendo do file handle antigo (agora `page_log.1`) após logrotate — novos jobs no `page_log` novo são perdidos.  
**Por que acontece:** File handle é amarrado ao inode, não ao path.  
**Como evitar:** Em cada ciclo de leitura, `os.stat(path).st_ino != self._inode` → fechar handle, reabrir, resetar offset para 0.  
**Sinal de alerta:** Jobs param de aparecer no banco após rotação de log.

### Pitfall 5: Volume cups_logs com permissões erradas no container backend
**O que dá errado:** `PermissionError: [Errno 13] Permission denied: '/var/log/cups/page_log'` no container backend.  
**Por que acontece:** O container CUPS escreve como `root`; o container backend pode rodar como usuário diferente.  
**Como evitar:** No `docker-compose.yml`, adicionar `user: root` ou configurar o usuário do container backend com acesso ao volume; alternativamente, garantir que o grupo `lp` (ou equivalente) tem leitura no volume.  
**Sinal de alerta:** Container backend sobe mas não processa nenhum job.

### Pitfall 6: Timestamp CUPS fora do UTC sem parse de fuso
**O que dá errado:** Timestamps persistidos sem fuso horário, causando queries de retenção incorretas.  
**Por que acontece:** O CUPS inclui offset no timestamp (`+0000` ou `-0300`), mas `strptime` sem `%z` descarta essa informação.  
**Como evitar:** Usar `datetime.strptime(ts_str, "%d/%b/%Y:%H:%M:%S %z")` — o `%z` lida com `+0000` e retorna `datetime` timezone-aware.  
**Sinal de alerta:** Purge por retenção remove jobs errados (muito cedo ou muito tarde).

### Pitfall 7: Parser crasha em linha malformada e para o watcher
**O que dá errado:** Uma linha inválida no page_log (ex.: linha de status CUPS, não de job) levanta exceção e mata o watcher.  
**Por que acontece:** `re.match()` retorna `None` para linhas que não casam; código sem verificação de `None` lança `AttributeError`.  
**Como evitar:** Sempre verificar `if m is None: logger.warning(...); continue` — descartar linhas que não casam com o regex (são informacionais do CUPS, não jobs).  
**Sinal de alerta:** Watcher para de processar jobs após linha de status do CUPS aparecer.

---

## Code Examples

### Verificado: Parse de timestamp CUPS

```python
# Source: Python stdlib datetime docs + formato CUPS confirmado em validate-phase1.sh
from datetime import datetime

def parse_cups_timestamp(raw: str) -> datetime:
    """
    raw: '26/May/2026:14:30:00 +0000'
    (já sem colchetes — grupo 4 do PAGE_LOG_REGEX)
    """
    return datetime.strptime(raw, "%d/%b/%Y:%H:%M:%S %z")
```

### Verificado: Parser de linha PAGE_LOG_REGEX

```python
# Source: PAGE_LOG_REGEX de scripts/validate-phase1.sh + PageLogFormat de cupsd.conf.template
import re
from typing import Optional

PAGE_LOG_REGEX = re.compile(
    r'^(\S+)\s+(\S+)\s+(\d+)\s+\[(.+?)\]\s+total\s+(\d+)\s+(\S+)\s+(\S+)\s+(.+?)\s+(\S+)\s+(\S+)$'
)

def _null_if_dash(value: str) -> Optional[str]:
    """D-09: valor sentinel '-' do CUPS → NULL no banco."""
    return None if value.strip() == "-" else value.strip()

def parse_page_log_line(line: str) -> Optional[dict]:
    m = PAGE_LOG_REGEX.match(line.strip())
    if m is None:
        return None   # linha de status CUPS ou formatação inesperada
    return {
        "printer":    m.group(1),
        "username":   m.group(2),          # D-08: sem normalização
        "job_id":     int(m.group(3)),
        "timestamp":  parse_cups_timestamp(m.group(4)),
        "pages":      int(m.group(5)),
        "color_mode": _null_if_dash(m.group(6)),
        "host_origin": _null_if_dash(m.group(7)),
        "job_name":   _null_if_dash(m.group(8)),
        "media":      _null_if_dash(m.group(9)),
        "sides":      _null_if_dash(m.group(10)),
        "copies":     None,  # não presente no PageLogFormat atual
        "status":     "allowed",            # D-15, EXTEND-01
    }
```

### Verificado: Purge por retenção (DATA-01)

```python
# Source: SQLAlchemy docs ORM delete + Python stdlib datetime
from datetime import datetime, timedelta, timezone
from sqlalchemy import delete

def purge_old_jobs(session, retention_days: int) -> int:
    """Retorna número de registros deletados."""
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=retention_days)
    result = session.execute(
        delete(PrintJob).where(PrintJob.timestamp < cutoff)
    )
    session.commit()
    return result.rowcount
```

### Verificado: Configuração SQLite para uso com threads (Source: SQLAlchemy docs)

```python
# Source: https://docs.sqlalchemy.org/en/20/dialects/sqlite.html
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    "sqlite:////app/data/printwatch.db",
    connect_args={"check_same_thread": False},
    poolclass=NullPool,
)
SessionLocal = sessionmaker(bind=engine)
```

---

## State of the Art

| Abordagem Antiga | Abordagem Atual | Mudou em | Impacto |
|------------------|-----------------|----------|---------|
| `Column(String)` no SQLAlchemy | `Mapped[str] = mapped_column()` | SQLAlchemy 2.0 (2023) | Type-safe, autocompletion, melhor integração com Pydantic |
| `Session = scoped_session(sessionmaker())` | `SessionLocal = sessionmaker(bind=engine)` + context manager | SQLAlchemy 2.0 | scoped_session ainda funciona, mas o padrão recomendado é context manager |
| `declarative_base()` (função) | `class Base(DeclarativeBase)` (classe) | SQLAlchemy 2.0 | Abordagem baseada em classe é type-safe; `declarative_base()` deprecated em 2.x |
| watchdog `PollingObserver` | watchdog `InotifyObserver` no Linux | watchdog 0.x | Zero polling overhead; InotifyObserver usa syscall do kernel |
| Polling manual com `os.stat()` | watchdog + `FileSystemEventHandler` | — | Reduz CPU de O(poll_interval) para 0 entre eventos |

**Deprecated/desatualizado:**
- `declarative_base()` como função standalone: substituído por `class Base(DeclarativeBase)` no SQLAlchemy 2.x — ainda funciona mas emite deprecation warning.
- watchdog `Observer` genérico em Linux: funciona mas `InotifyObserver` explícito é recomendado em containers Linux para garantir que não há fallback para polling.

---

## Assumptions Log

| # | Afirmação | Seção | Risco se errado |
|---|-----------|-------|-----------------|
| A1 | O campo `%C` (group 6 no regex) e `%{job-billing}` (group 7) correspondem a color_mode e host_origin respectivamente, baseado na linha de amostra de `validate-phase1.sh` | Mapeamento PAGE_LOG_REGEX | Se a ordem dos campos no log real diferir, campos seriam persistidos na coluna errada — verificar com `docker compose exec cups tail /var/log/cups/page_log` após um job real |
| A2 | O campo `copies` não está presente no `PageLogFormat` atual e será NULL no MVP | Schema | Se CUPS gravar copies em algum campo não mapeado, a informação é perdida |
| A3 | O container backend rodará como root (ou usuário com acesso ao volume cups_logs) | Docker | Se run como usuário não-root sem permissão, watcher falha silenciosamente |
| A4 | Logrotate não está configurado na Fase 2 (sem rotação ativa), mas o mecanismo de inode é implementado de qualquer forma para preparação futura (D-07) | TailReader | Sem impacto no MVP — o código de detecção de inode não tem custo quando o inode não muda |
| A5 | Python 3.11+ disponível na imagem Docker base (`python:3.11-slim`) | Dockerfile | `Mapped[T]` e `mapped_column` exigem Python 3.9+; 3.11 recomendado para FastAPI 0.136.x |

---

## Open Questions (RESOLVED)

1. **Mapeamento exato dos grupos 6 e 7 do PAGE_LOG_REGEX** ✅ RESOLVED
   - O que sabemos: `PageLogFormat` tem `%C %{job-billing}` e a amostra mostra `-` (grupo 6) e `192.168.1.10` (grupo 7).
   - **Decisão:** Implementar parser com grupo 6 = `billing/color_mode` (valor CUPS `%C` — pode ser `color`, `mono`, ou `-`) e grupo 7 = `host_origin` (IP/hostname do cliente). NULL via `_null_if_dash()` para valores `-`. O script `validate-phase2.sh` imprime os grupos capturados de uma linha real após deploy para confirmar o mapeamento em ambiente de produção HP/Samsung.

2. **Estrutura mínima de `policies` (EXTEND-02)** ✅ RESOLVED
   - **Decisão (Claude's Discretion):** Criar tabela `policies` com colunas mínimas `id` (Integer PK), `name` (String), `created_at` (DateTime) — suficiente para EXTEND-02 sem Alembic; schema de regras adicionado na Fase 3+ quando as regras de políticas forem definidas.

3. **Process manager do watcher dentro do container FastAPI** ✅ RESOLVED
   - **Decisão (Claude's Discretion):** Thread daemon via `lifespan` context manager do FastAPI — `observer.start()` antes do yield, `observer.stop()` no shutdown. Padrão mais simples sem subprocesso adicional; alinhado com D-11 (único container) e D-13 (componentes ativos no mesmo processo).

---

## Environment Availability

| Dependência | Requerida por | Disponível | Versão | Fallback |
|-------------|--------------|------------|--------|----------|
| Docker + Docker Compose | Container backend, volume db_data | ✓ | Instalado na VM VM_HOST (evidência Fase 1) | — |
| Python 3.9+ (no container) | watchdog, SQLAlchemy 2.x, FastAPI | ✓ (via imagem) | `python:3.11-slim` recomendado | `python:3.10-slim` (watchdog exige 3.9+) |
| inotify (kernel Linux) | InotifyObserver | ✓ | Ubuntu 22.04 LTS — inotify presente | PollingObserver como fallback (adiciona ~1s latência) |
| Volume cups_logs | Leitura do page_log | ✓ | Já criado na Fase 1 em `docker-compose.yml` | — |
| Volume db_data (novo) | Persistência do SQLite | ✗ (ainda não criado) | — | Será criado ao adicionar o serviço `backend` no compose |

**Dependências faltando sem fallback:** `db_data` — será criado no Wave 1 da implementação junto com o serviço `backend` no compose.

**Dependências faltando com fallback:**
- Se inotify não estiver disponível (container rootless sem capabilities), usar `PollingObserver` como fallback — adiciona ~1s de latência mas satisfaz CAPTURE-02 (≤ 30s).

---

## Validation Architecture

### Test Framework

| Propriedade | Valor |
|-------------|-------|
| Framework | pytest (padrão Python; nenhum detectado no repo atual — instalar no Wave 0) |
| Arquivo de config | `backend/pytest.ini` ou `backend/pyproject.toml` (criar no Wave 0) |
| Comando rápido | `pytest backend/tests/ -x -q` |
| Suite completa | `pytest backend/tests/ -v` + `bash scripts/validate-phase2.sh --quick` |

### Mapeamento Requisitos → Testes

| Req ID | Comportamento | Tipo de Teste | Comando Automatizado | Arquivo Existe? |
|--------|---------------|---------------|---------------------|-----------------|
| CAPTURE-01 | Parser mapeia todos os campos da linha sample | unit | `pytest backend/tests/test_parser.py::test_all_fields_mapped -x` | ❌ Wave 0 |
| CAPTURE-01 | NULL para campo `-` (D-09) | unit | `pytest backend/tests/test_parser.py::test_null_for_dash -x` | ❌ Wave 0 |
| CAPTURE-02 | Job chega ao banco em ≤ 30s | manual/smoke | `bash scripts/validate-phase2.sh` (full) | ❌ Wave 0 |
| CAPTURE-03 | Restart sem duplicata (mesmo inode) | unit/integration | `pytest backend/tests/test_tail_reader.py::test_seek_on_restart -x` | ❌ Wave 0 |
| CAPTURE-03 | Inode diferente → reprocessamento do início | unit | `pytest backend/tests/test_tail_reader.py::test_inode_change_reopen -x` | ❌ Wave 0 |
| DATA-01 | Purge deleta registros antigos | unit | `pytest backend/tests/test_retention.py::test_purge_old_jobs -x` | ❌ Wave 0 |
| DATA-03 | SQLite com permissões 600 | smoke | `bash scripts/validate-phase2.sh --quick` (check stat) | ❌ Wave 0 |
| EXTEND-01 | status default `allowed` | unit | `pytest backend/tests/test_models.py::test_status_default -x` | ❌ Wave 0 |
| EXTEND-03 | `pre_process_job` retorna `True` | unit | `pytest backend/tests/test_service.py::test_hook_returns_true -x` | ❌ Wave 0 |

### Gaps do Wave 0

- [ ] `backend/tests/__init__.py` — pacote de testes
- [ ] `backend/tests/conftest.py` — fixtures: engine in-memory SQLite, sessão, sample line
- [ ] `backend/tests/test_parser.py` — cobre CAPTURE-01, D-08, D-09
- [ ] `backend/tests/test_tail_reader.py` — cobre CAPTURE-03 (seek + inode)
- [ ] `backend/tests/test_retention.py` — cobre DATA-01
- [ ] `backend/tests/test_models.py` — cobre EXTEND-01, EXTEND-02
- [ ] `backend/tests/test_service.py` — cobre EXTEND-03
- [ ] `backend/pytest.ini` — config mínima (`testpaths = tests`)
- [ ] Instalação: `pip install pytest pytest-cov` no `requirements.txt` do backend
- [ ] `scripts/validate-phase2.sh` — espelho do validate-phase1.sh; testa container backend + DB + permissões

---

## Security Domain

### Categorias ASVS Aplicáveis

| Categoria ASVS | Aplica | Controle Padrão |
|----------------|--------|-----------------|
| V2 Authentication | Não | Sem autenticação na Fase 2 (D-12) |
| V3 Session Management | Não | Sem sessões de usuário na Fase 2 |
| V4 Access Control | Parcial | Volume `cups_logs` montado `:ro`; SQLite com permissões 600 (DATA-03) |
| V5 Input Validation | Sim | `PAGE_LOG_REGEX` como schema de validação de entrada; linhas que não casam são descartadas (não crasha) |
| V6 Cryptography | Não | Dados em repouso não criptografados (SQLite local, rede interna); aceitável para MVP em rede local |

### Ameaças Conhecidas para o Stack

| Padrão | STRIDE | Mitigação Padrão |
|--------|--------|-----------------|
| Injeção via conteúdo malicioso no page_log | Tampering | SQLAlchemy ORM com parâmetros vinculados — nunca interpolação de string em SQL |
| Acesso direto ao arquivo SQLite pela rede | Information Disclosure | DATA-03: `chmod 600`; volume `db_data` não exposto; sem porta de banco na rede |
| Watcher com acesso de escrita ao volume CUPS | Elevation of Privilege | Volume montado `:ro` no compose — CUPS não pode ser corrompido pelo backend |
| Parada do watcher sem supervisão | Denial of Service | `restart: unless-stopped` no compose; healthcheck interno detecta watcher parado |

---

## Sources

### Primárias (HIGH confidence)
- `/gorakhargosh/watchdog` via Context7 — FileSystemEventHandler, Observer, InotifyObserver, PollingObserver [CITED: https://context7.com/gorakhargosh/watchdog/llms.txt]
- `/websites/sqlalchemy_en_20` via Context7 — DeclarativeBase, mapped_column, NullPool, ON CONFLICT DO NOTHING [CITED: https://docs.sqlalchemy.org/en/20/]
- PyPI `pip index versions` — versões atuais de watchdog (6.0.0), sqlalchemy (2.0.50), fastapi (0.136.3), uvicorn (0.48.0) [VERIFIED: PyPI registry]
- `scripts/validate-phase1.sh` — PAGE_LOG_REGEX e linha de amostra [VERIFIED: codebase]
- `cups/cupsd.conf.template` — PageLogFormat com ordem de campos [VERIFIED: codebase]

### Secundárias (MEDIUM confidence)
- StackOverflow "Detect log file rotation while watching log file" — padrão inode-check com `os.stat().st_ino` [CITED: stackoverflow.com/questions/44407834]
- StackOverflow "rotate reopen file in python3" — padrão inode comparison loop [CITED: stackoverflow.com/questions/62036007]
- SQLAlchemy docs sqlite dialect — `on_conflict_do_nothing`, connection string com 4 barras [CITED: docs.sqlalchemy.org/en/20/dialects/sqlite.html]

### Terciárias (LOW confidence)
- Nenhuma — todos os claims críticos foram verificados via fontes primárias ou secundárias.

---

## Metadata

**Breakdown de confiança:**
- Stack padrão: HIGH — versões verificadas via PyPI; bibliotecas com alta reputação e documentação oficial
- Arquitetura: HIGH — padrões derivados de código existente (Fase 1) + documentação oficial
- Pitfalls: HIGH — verificados em múltiplas fontes (docs oficiais + StackOverflow cross-referenciado)
- Mapeamento PAGE_LOG_REGEX: MEDIUM — baseado em regex existente + amostra real; grupos 6/7 marcados [ASSUMED] pendente validação com job real na VM

**Data da pesquisa:** 2026-05-26  
**Válido até:** 2026-06-25 (bibliotecas estáveis; watchdog e SQLAlchemy têm releases minor frequentes mas API estável)
