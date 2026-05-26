from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PrintJob(Base):
    __tablename__ = "print_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    printer: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    job_id: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    pages: Mapped[int] = mapped_column(Integer, nullable=False)
    color_mode: Mapped[Optional[str]] = mapped_column(String(50))
    host_origin: Mapped[Optional[str]] = mapped_column(String(255))
    job_name: Mapped[Optional[str]] = mapped_column(String(512))
    media: Mapped[Optional[str]] = mapped_column(String(100))
    sides: Mapped[Optional[str]] = mapped_column(String(50))
    copies: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="allowed"
    )

    __table_args__ = (
        UniqueConstraint(
            "printer",
            "job_id",
            "timestamp",
            "pages",
            name="uq_page_log_line",
        ),
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
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
