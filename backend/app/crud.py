"""Database operations for patients. Routes in main.py call these."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .constants import DEFAULT_DOCTORS, DEFAULT_WARDS
from .models import Doctor, Patient, Ward
from .schemas import PatientIn

# ---------- Lookup tables (wards, doctors) ----------
# Both tables have the same shape (id, name), so the same helpers work for both.


def seed_lookup_tables(db: Session) -> None:
    """Fill the wards and doctors tables with defaults, only if they are empty."""
    for model, defaults in ((Ward, DEFAULT_WARDS), (Doctor, DEFAULT_DOCTORS)):
        if db.scalar(select(model.id).limit(1)) is None:
            db.add_all(model(name=name) for name in defaults)
    db.commit()


def list_names(db: Session, model) -> list[str]:
    """All names from the wards or doctors table, alphabetically."""
    return list(db.scalars(select(model.name).order_by(model.name)))


def name_exists(db: Session, model, name: str) -> bool:
    return db.scalar(select(model.id).where(model.name == name)) is not None


# ---------- Patients ----------


def list_patients(
    db: Session,
    search: str | None = None,
    ward: str | None = None,
    department: str | None = None,
    doctor: str | None = None,
    status: str | None = None,
) -> list[Patient]:
    query = select(Patient)
    if search and search.strip():
        # Case-insensitive "contains" match on the name.
        query = query.where(Patient.name.ilike(f"%{search.strip()}%"))
    if ward:
        query = query.where(Patient.ward == ward)
    if department:
        query = query.where(Patient.department == department)
    if doctor:
        query = query.where(Patient.doctor == doctor)
    if status:
        query = query.where(Patient.status == status)
    query = query.order_by(Patient.id.desc())  # newest first
    return list(db.scalars(query))


def get_patient(db: Session, patient_id: int) -> Patient | None:
    return db.get(Patient, patient_id)


def create_patient(db: Session, data: PatientIn) -> Patient:
    patient = Patient(**data.model_dump())
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def update_patient(db: Session, patient: Patient, data: PatientIn) -> Patient:
    for field, value in data.model_dump().items():
        setattr(patient, field, value)
    db.commit()
    db.refresh(patient)
    return patient


def discharge_patient(db: Session, patient: Patient) -> Patient:
    patient.status = "Discharged"
    db.commit()
    db.refresh(patient)
    return patient


def delete_patient(db: Session, patient: Patient) -> None:
    db.delete(patient)
    db.commit()
