"""FastAPI application: routes, CORS and error handling."""

import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from . import crud
from .constants import DEPARTMENTS, GENDERS, STATUSES
from .database import Base, SessionLocal, engine, get_db
from .models import Doctor, Ward
from .schemas import PatientIn, PatientOut


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create the tables on startup if they don't exist, and fill the wards and
    # doctors tables with defaults the first time.
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        crud.seed_lookup_tables(db)
    yield


app = FastAPI(title="Patient Admission Management API", lifespan=lifespan)

# Only the frontend origins listed in FRONTEND_ORIGIN (comma separated) may call the API.
origins = [
    o.strip()
    for o in os.getenv("FRONTEND_ORIGIN", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Clear validation error messages ----------

FIELD_LABELS = {
    "name": "Name",
    "age": "Age",
    "gender": "Gender",
    "ward": "Ward",
    "department": "Department",
    "doctor": "Doctor",
    "admission_date": "Admission date",
    "status": "Status",
}


def _friendly_message(field: str, error: dict) -> str:
    label = FIELD_LABELS.get(field, field)
    err_type = error.get("type", "")
    if err_type == "missing":
        return f"{label} is required"
    if err_type == "value_error":
        # Messages raised in our own validators ("Value error, <msg>").
        return error["msg"].removeprefix("Value error, ")
    if field == "age":
        return "Age must be a whole number"
    if field == "admission_date":
        return "Admission date must be a valid date (YYYY-MM-DD)"
    if err_type == "string_type":
        return f"{label} must be text"
    return f"{label}: {error.get('msg', 'invalid value')}"


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Turn Pydantic's raw errors into {"field": "readable message"}."""
    errors: dict[str, str] = {}
    for error in exc.errors():
        loc = [str(part) for part in error.get("loc", []) if part != "body"]
        field = loc[0] if loc else "body"
        if field == "body":
            errors.setdefault("body", "Request body must be a valid JSON object")
            continue
        errors.setdefault(field, _friendly_message(field, error))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation failed: " + "; ".join(errors.values()), "errors": errors},
    )


def _check_ward_and_doctor_exist(db: Session, data: PatientIn) -> None:
    """Backend check that the chosen ward and doctor are in their tables.

    Raised as a normal validation error, so the response has the same
    {"detail", "errors": {"ward": ..., "doctor": ...}} shape as every other field.
    """
    errors = []
    for field, model, label in (("ward", Ward, "Ward"), ("doctor", Doctor, "Doctor")):
        if not crud.name_exists(db, model, getattr(data, field)):
            allowed = ", ".join(crud.list_names(db, model))
            errors.append({
                "type": "value_error",
                "loc": ("body", field),
                "msg": f"Value error, {label} must be one of: {allowed}",
            })
    if errors:
        raise RequestValidationError(errors)


def _get_or_404(db: Session, patient_id: int):
    patient = crud.get_patient(db, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail=f"Patient with id {patient_id} not found")
    return patient


# ---------- Routes ----------

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/options")
def options(db: Session = Depends(get_db)):
    """Dropdown values for the frontend. Wards and doctors come from the database."""
    return {
        "genders": GENDERS,
        "wards": crud.list_names(db, Ward),
        "departments": DEPARTMENTS,
        "doctors": crud.list_names(db, Doctor),
        "statuses": STATUSES,
    }


@app.get("/api/wards")
def list_wards(db: Session = Depends(get_db)):
    return crud.list_names(db, Ward)


@app.get("/api/doctors")
def list_doctors(db: Session = Depends(get_db)):
    return crud.list_names(db, Doctor)


@app.get("/api/patients", response_model=list[PatientOut])
def list_patients(
    search: str | None = None,
    ward: str | None = None,
    department: str | None = None,
    doctor: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    return crud.list_patients(db, search, ward, department, doctor, status)


@app.get("/api/patients/{patient_id}", response_model=PatientOut)
def get_patient(patient_id: int, db: Session = Depends(get_db)):
    return _get_or_404(db, patient_id)


@app.post("/api/patients", response_model=PatientOut, status_code=201)
def create_patient(data: PatientIn, db: Session = Depends(get_db)):
    _check_ward_and_doctor_exist(db, data)
    return crud.create_patient(db, data)


@app.put("/api/patients/{patient_id}", response_model=PatientOut)
def update_patient(patient_id: int, data: PatientIn, db: Session = Depends(get_db)):
    patient = _get_or_404(db, patient_id)
    _check_ward_and_doctor_exist(db, data)
    return crud.update_patient(db, patient, data)


@app.patch("/api/patients/{patient_id}/discharge", response_model=PatientOut)
def discharge_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = _get_or_404(db, patient_id)
    if patient.status == "Discharged":
        raise HTTPException(status_code=400, detail="Patient is already discharged")
    return crud.discharge_patient(db, patient)


@app.delete("/api/patients/{patient_id}", status_code=200)
def delete_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = _get_or_404(db, patient_id)
    crud.delete_patient(db, patient)
    return {"message": f"Patient {patient.name} deleted"}
