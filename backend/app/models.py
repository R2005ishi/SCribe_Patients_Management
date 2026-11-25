"""SQLAlchemy table definitions: doctors and patients."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Doctor(Base):
    """Doctors that a patient can be assigned to (fills the Doctor dropdown)."""

    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)


class Ward(Base):
    """Hospital wards a patient can be admitted to (fills the Ward dropdown)."""

    __tablename__ = "wards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    ward: Mapped[str] = mapped_column(String(50), ForeignKey("wards.name"), nullable=False)
    department: Mapped[str] = mapped_column(String(50), nullable=False)
    # ward/doctor are foreign keys to wards.name/doctors.name: the database itself
    # refuses a value that isn't in those tables, and won't let a ward or doctor
    # that still has patients be deleted.
    doctor: Mapped[str] = mapped_column(String(50), ForeignKey("doctors.name"), nullable=False)
    admission_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="Admitted")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
