"""Pydantic schemas = backend validation.

Every request body for create/update goes through PatientIn. If any rule fails,
FastAPI raises a validation error, which main.py turns into a clear message per
field (see validation_exception_handler).
"""

import re
from datetime import date, datetime, timedelta, timezone

from pydantic import BaseModel, ConfigDict, field_validator

from .constants import DEPARTMENTS, GENDERS, STATUSES

# Letters only; single spaces allowed between words (e.g. "Rishi Agrawal").
NAME_PATTERN = re.compile(r"^[A-Za-z]+( [A-Za-z]+)*$")

# The hospital works in IST. Servers usually run in UTC, so "today" is computed
# in IST - otherwise a patient admitted just after midnight IST would be
# rejected as a "future" date.
IST = timezone(timedelta(hours=5, minutes=30))


def today_ist() -> date:
    return datetime.now(IST).date()


def _required(value: str, label: str) -> str:
    value = (value or "").strip()
    if not value:
        raise ValueError(f"{label} is required")
    return value


def _check_choice(value: str, allowed: list[str], label: str) -> str:
    value = _required(value, label)
    if value not in allowed:
        raise ValueError(f"{label} must be one of: {', '.join(allowed)}")
    return value


class PatientIn(BaseModel):
    """Body for POST /api/patients and PUT /api/patients/{id}."""

    name: str
    age: int
    gender: str
    ward: str
    department: str
    doctor: str
    admission_date: date
    status: str = "Admitted"

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = " ".join(v.split())  # trim and collapse repeated spaces
        if not v:
            raise ValueError("Name is required")
        if len(v) > 100:
            raise ValueError("Name must be at most 100 characters")
        if not NAME_PATTERN.match(v):
            raise ValueError("Name must contain letters only")
        return v

    @field_validator("age")
    @classmethod
    def validate_age(cls, v: int) -> int:
        if v < 0 or v > 120:
            raise ValueError("Age must be between 0 and 120")
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        return _check_choice(v, GENDERS, "Gender")

    @field_validator("ward")
    @classmethod
    def validate_ward(cls, v: str) -> str:
        # Existence in the wards table is checked in main.py (needs the DB).
        return _required(v, "Ward")

    @field_validator("department")
    @classmethod
    def validate_department(cls, v: str) -> str:
        return _check_choice(v, DEPARTMENTS, "Department")

    @field_validator("doctor")
    @classmethod
    def validate_doctor(cls, v: str) -> str:
        # Existence in the doctors table is checked in main.py (needs the DB).
        return _required(v, "Doctor")

    @field_validator("admission_date")
    @classmethod
    def validate_admission_date(cls, v: date) -> date:
        if v > today_ist():
            raise ValueError("Admission date cannot be a future date")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        return _check_choice(v, STATUSES, "Status")


class PatientOut(BaseModel):
    """What the API returns for a patient."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    age: int
    gender: str
    ward: str
    department: str
    doctor: str
    admission_date: date
    status: str
