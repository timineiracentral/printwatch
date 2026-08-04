from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.simpress.config import simpress_settings
from app.simpress.db.base import SimpressBase
from app.simpress.db import models  # noqa: F401

_db_url = f"sqlite:///{simpress_settings.db_path}"

simpress_engine = create_engine(
    _db_url,
    connect_args={"check_same_thread": False},
    poolclass=NullPool,
)
SimpressSessionLocal = sessionmaker(bind=simpress_engine)


def get_simpress_db() -> Generator[Session, None, None]:
    """Generator para FastAPI Depends() — injeta Session Simpress isolada."""
    db = SimpressSessionLocal()
    try:
        yield db
    finally:
        db.close()
