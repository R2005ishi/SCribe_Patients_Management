from datetime import timedelta

import pytest

from app.schemas import today_ist

VALID = {
    "name": "Rishi Agrawal",
    "age": 30,
    "gender": "Male",
    "ward": "ICU",
    "department": "Cardiology",
    "doctor": "Dr. Anil Sharma",
    "admission_date": today_ist().isoformat(),
}


def create(client, **overrides):
    return client.post("/api/patients", json={**VALID, **overrides})


def test_create_and_list(client):
    r = create(client)
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "Admitted"
    assert body["name"] == "Rishi Agrawal"
    assert len(client.get("/api/patients").json()) == 1


@pytest.mark.parametrize(
    "field,value,message",
    [
        ("name", "", "Name is required"),
        ("name", "John123", "Name must contain letters only"),
        ("name", "J@hn", "Name must contain letters only"),
        ("age", -1, "Age must be between 0 and 120"),
        ("age", 121, "Age must be between 0 and 120"),
        ("age", "abc", "Age must be a whole number"),
        ("gender", "", "Gender is required"),
        ("ward", "Rooftop", "Ward must be one of"),
        ("department", "Magic", "Department must be one of"),
        ("doctor", "Dr. Nobody", "Doctor must be one of"),
        ("admission_date", (today_ist() + timedelta(days=1)).isoformat(),
         "Admission date cannot be a future date"),
        ("admission_date", "not-a-date", "Admission date must be a valid date"),
        ("status", "Sleeping", "Status must be one of"),
    ],
)
def test_backend_rejects_bad_data(client, field, value, message):
    r = create(client, **{field: value})
    assert r.status_code == 422
    assert message in r.json()["errors"][field]
    assert client.get("/api/patients").json() == []  # nothing saved


def test_missing_fields(client):
    r = client.post("/api/patients", json={})
    assert r.status_code == 422
    errors = r.json()["errors"]
    for field in ["name", "age", "gender", "ward", "department", "doctor", "admission_date"]:
        assert errors[field].endswith("is required")


def test_age_boundaries_allowed(client):
    assert create(client, age=0).status_code == 201
    assert create(client, age=120).status_code == 201


def test_filters_and_search(client):
    create(client, name="Asha Patel", ward="ICU", department="Cardiology", doctor="Dr. Anil Sharma")
    create(client, name="Ravi Kumar", ward="General Ward", department="Neurology", doctor="Dr. Priya Nair")
    create(client, name="Ashok Singh", ward="General Ward", department="Cardiology", doctor="Dr. Priya Nair")

    names = lambda r: sorted(p["name"] for p in r.json())  # noqa: E731
    assert names(client.get("/api/patients", params={"search": "ash"})) == ["Asha Patel", "Ashok Singh"]
    assert names(client.get("/api/patients", params={"ward": "General Ward"})) == ["Ashok Singh", "Ravi Kumar"]
    assert names(client.get("/api/patients", params={"department": "Cardiology", "doctor": "Dr. Priya Nair"})) == ["Ashok Singh"]


def test_doctors_come_from_database(client):
    from app.constants import DEFAULT_DOCTORS
    from app.database import SessionLocal
    from app.models import Doctor

    # Seeded on startup and served to the frontend dropdown.
    assert sorted(client.get("/api/options").json()["doctors"]) == sorted(DEFAULT_DOCTORS)
    assert sorted(client.get("/api/doctors").json()) == sorted(DEFAULT_DOCTORS)

    # A doctor added to the table becomes valid for patients immediately.
    assert create(client, doctor="Dr. New Joiner").status_code == 422
    with SessionLocal() as db:
        db.add(Doctor(name="Dr. New Joiner"))
        db.commit()
    assert "Dr. New Joiner" in client.get("/api/options").json()["doctors"]
    assert create(client, doctor="Dr. New Joiner").status_code == 201


def test_wards_come_from_database(client):
    from app.constants import DEFAULT_WARDS
    from app.database import SessionLocal
    from app.models import Ward

    assert sorted(client.get("/api/options").json()["wards"]) == sorted(DEFAULT_WARDS)
    assert sorted(client.get("/api/wards").json()) == sorted(DEFAULT_WARDS)

    assert create(client, ward="Burns Unit").status_code == 422
    with SessionLocal() as db:
        db.add(Ward(name="Burns Unit"))
        db.commit()
    assert create(client, ward="Burns Unit").status_code == 201


def test_unknown_ward_and_doctor_both_reported(client):
    r = create(client, ward="Rooftop", doctor="Dr. Ghost")
    assert r.status_code == 422
    errors = r.json()["errors"]
    assert "Ward must be one of" in errors["ward"]
    assert "Doctor must be one of" in errors["doctor"]


def test_edit_with_unknown_doctor_rejected(client):
    pid = create(client).json()["id"]
    r = client.put(f"/api/patients/{pid}", json={**VALID, "doctor": "Dr. Ghost"})
    assert r.status_code == 422
    assert "Doctor must be one of" in r.json()["errors"]["doctor"]


def test_edit_discharge_delete(client):
    pid = create(client).json()["id"]

    r = client.put(f"/api/patients/{pid}", json={**VALID, "name": "Rishi A", "age": 31})
    assert r.status_code == 200 and r.json()["age"] == 31

    assert client.put(f"/api/patients/{pid}", json={**VALID, "age": 500}).status_code == 422

    r = client.patch(f"/api/patients/{pid}/discharge")
    assert r.status_code == 200 and r.json()["status"] == "Discharged"
    assert client.patch(f"/api/patients/{pid}/discharge").status_code == 400

    assert client.delete(f"/api/patients/{pid}").status_code == 200
    assert client.get(f"/api/patients/{pid}").status_code == 404
    assert client.delete(f"/api/patients/{pid}").status_code == 404
