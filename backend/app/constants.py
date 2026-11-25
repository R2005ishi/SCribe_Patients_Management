"""Allowed values for the dropdown fields.

This is the single source of truth: the backend validates against these lists
and the frontend loads them from GET /api/options, so the two never drift apart.
To add a new gender/department, just add it here.

Wards and doctors live in the `wards` and `doctors` database tables.
DEFAULT_WARDS / DEFAULT_DOCTORS are only used to fill those tables the first
time the app starts (when a table is empty).
"""

GENDERS = ["Male", "Female", "Other"]

DEFAULT_WARDS = ["General Ward", "ICU", "Emergency", "Pediatric Ward", "Maternity Ward", "Surgical Ward"]

DEPARTMENTS = [
    "General Medicine",
    "Cardiology",
    "Neurology",
    "Orthopedics",
    "Pediatrics",
    "Gynecology",
]

DEFAULT_DOCTORS = [
    "Dr. Anil Sharma",
    "Dr. Priya Nair",
    "Dr. Rahul Verma",
    "Dr. Sneha Iyer",
    "Dr. Vikram Rao",
    "Dr. Meera Kapoor",
]

STATUSES = ["Admitted", "Discharged"]
