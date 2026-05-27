from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CostCenter(Base):
    __tablename__ = "cost_centers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    departments: Mapped[list["Department"]] = relationship(back_populates="cost_center")
    users: Mapped[list["User"]] = relationship(back_populates="cost_center")


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    cost_center_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("cost_centers.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    cost_center: Mapped[Optional["CostCenter"]] = relationship(
        back_populates="departments"
    )
    users: Mapped[list["User"]] = relationship(back_populates="department")
    printers: Mapped[list["Printer"]] = relationship(back_populates="department")


class Printer(Base):
    __tablename__ = "printers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    cups_queue_name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    manufacturer_model: Mapped[Optional[str]] = mapped_column(String(255))
    location: Mapped[Optional[str]] = mapped_column(String(255))
    department_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("departments.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    department: Mapped[Optional["Department"]] = relationship(back_populates="printers")
    print_jobs: Mapped[list["PrintJob"]] = relationship(back_populates="printer_ref")
    user_access_rows: Mapped[list["UserPrinterAccess"]] = relationship(
        back_populates="printer"
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cups_username: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id"), nullable=False
    )
    cost_center_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("cost_centers.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    department: Mapped["Department"] = relationship(back_populates="users")
    cost_center: Mapped[Optional["CostCenter"]] = relationship(back_populates="users")
    printer_access_rows: Mapped[list["UserPrinterAccess"]] = relationship(
        back_populates="user"
    )


class UserPrinterAccess(Base):
    __tablename__ = "user_printer_access"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    printer_id: Mapped[int] = mapped_column(ForeignKey("printers.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    user: Mapped["User"] = relationship(back_populates="printer_access_rows")
    printer: Mapped["Printer"] = relationship(back_populates="user_access_rows")

    __table_args__ = (
        UniqueConstraint("user_id", "printer_id", name="uq_user_printer"),
    )


class PrintJob(Base):
    __tablename__ = "print_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    printer: Mapped[str] = mapped_column(String(255), nullable=False)
    printer_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("printers.id"), nullable=True
    )
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

    printer_ref: Mapped[Optional["Printer"]] = relationship(back_populates="print_jobs")

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
