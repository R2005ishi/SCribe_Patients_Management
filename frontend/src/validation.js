// Frontend validation - the same rules the backend enforces in schemas.py.

// Letters only; single spaces allowed between words (e.g. "Rishi Agrawal").
const NAME_PATTERN = /^[A-Za-z]+( [A-Za-z]+)*$/;

// Today's date as "YYYY-MM-DD" in the user's local time zone.
export function todayString() {
  const d = new Date();
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  return `${d.getFullYear()}-${mm}-${dd}`;
}

function checkChoice(value, allowed, label) {
  if (!value) return `${label} is required`;
  if (allowed && !allowed.includes(value)) return `${label} must be selected from the list`;
  return null;
}

// Returns an object of { field: message } - empty when the form is valid.
export function validatePatient(form, options) {
  const errors = {};

  const name = form.name.trim().replace(/\s+/g, " ");
  if (!name) errors.name = "Name is required";
  else if (name.length > 100) errors.name = "Name must be at most 100 characters";
  else if (!NAME_PATTERN.test(name)) errors.name = "Name must contain letters only";

  if (form.age === "" || form.age === null) errors.age = "Age is required";
  else if (!/^\d+$/.test(String(form.age))) errors.age = "Age must be a whole number";
  else if (Number(form.age) < 0 || Number(form.age) > 120) errors.age = "Age must be between 0 and 120";

  const choices = [
    ["gender", options?.genders, "Gender"],
    ["ward", options?.wards, "Ward"],
    ["department", options?.departments, "Department"],
    ["doctor", options?.doctors, "Doctor"],
  ];
  for (const [field, allowed, label] of choices) {
    const message = checkChoice(form[field], allowed, label);
    if (message) errors[field] = message;
  }

  if (!form.admission_date) errors.admission_date = "Admission date is required";
  else if (form.admission_date > todayString())
    errors.admission_date = "Admission date cannot be a future date";

  return errors;
}
