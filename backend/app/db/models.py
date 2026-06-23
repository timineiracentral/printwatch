from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
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
    snmp_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    snmp_community_override: Mapped[Optional[str]] = mapped_column(String(255))
    # NULL = não configurado = color-capable (compatibilidade retroativa); valores: "mono_only" | "color" | NULL
    color_capability: Mapped[Optional[str]] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    department: Mapped[Optional["Department"]] = relationship(back_populates="printers")
    print_jobs: Mapped[list["PrintJob"]] = relationship(back_populates="printer_ref")
    meter_readings: Mapped[list["PrinterMeterReading"]] = relationship(
        back_populates="printer"
    )
    user_access_rows: Mapped[list["UserPrinterAccess"]] = relationship(
        back_populates="printer"
    )
    fleet_status: Mapped[Optional["PrinterFleetStatus"]] = relationship(
        back_populates="printer", uselist=False
    )
    toner_snapshot: Mapped[Optional["PrinterTonerSnapshot"]] = relationship(
        back_populates="printer", uselist=False
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


class PrinterFleetStatus(Base):
    __tablename__ = "printer_fleet_status"

    printer_id: Mapped[int] = mapped_column(
        ForeignKey("printers.id", ondelete="CASCADE"), primary_key=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    last_checked_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(String(512))

    printer: Mapped["Printer"] = relationship(back_populates="fleet_status")


class PrinterTonerSnapshot(Base):
    __tablename__ = "printer_toner_snapshots"

    printer_id: Mapped[int] = mapped_column(
        ForeignKey("printers.id", ondelete="CASCADE"), primary_key=True
    )
    black_pct: Mapped[Optional[int]] = mapped_column(Integer)
    color_pct: Mapped[Optional[int]] = mapped_column(Integer)
    partial_color: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    printer: Mapped["Printer"] = relationship(back_populates="toner_snapshot")


class PrinterMeterReading(Base):
    __tablename__ = "printer_meter_readings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    printer_id: Mapped[int] = mapped_column(ForeignKey("printers.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    counter_total: Mapped[int] = mapped_column(Integer, nullable=False)
    counter_mono: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    counter_color: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    printer: Mapped["Printer"] = relationship(back_populates="meter_readings")


class CostRate(Base):
    __tablename__ = "cost_rates"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rate_mono: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    rate_color: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    valid_from: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


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
    color_mode_source: Mapped[Optional[str]] = mapped_column(String(20))
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
