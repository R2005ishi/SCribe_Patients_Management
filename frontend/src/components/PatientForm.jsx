import { useState } from "react";
import Modal from "./Modal.jsx";
import { todayString, validatePatient } from "../validation.js";

const emptyForm = () => ({
  name: "",
  age: "",
  gender: "",
  ward: "",
  department: "",
  doctor: "",
  admission_date: todayString(),
  status: "Admitted",
});

// Add / Edit form in a popup. `patient` is null when adding.
export default function PatientForm({ patient, options, onSubmit, onClose }) {
  const isEdit = Boolean(patient);
  const [form, setForm] = useState(() => (patient ? { ...patient, age: String(patient.age) } : emptyForm()));
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);

  const update = (field) => (e) => {
    setForm({ ...form, [field]: e.target.value });
    if (errors[field]) setErrors({ ...errors, [field]: undefined }); // clear error while typing
  };

  async function handleSubmit(e) {
    e.preventDefault();
    setFormError("");

    // 1) Frontend validation
    const found = validatePatient(form, options);
    setErrors(found);
    if (Object.keys(found).length > 0) return;

    // 2) Send to backend (which validates again)
    const payload = {
      name: form.name.trim().replace(/\s+/g, " "),
      age: Number(form.age),
      gender: form.gender,
      ward: form.ward,
      department: form.department,
      doctor: form.doctor,
      admission_date: form.admission_date,
      status: form.status,
    };
    setSaving(true);
    try {
      await onSubmit(payload);
    } catch (err) {
      // Show backend validation messages under the matching fields.
      setErrors(err.fieldErrors || {});
      setFormError(err.message);
      setSaving(false);
    }
  }

  const field = (name, label, input) => (
    <div className={`form-field ${errors[name] ? "has-error" : ""}`}>
      <label htmlFor={`f-${name}`}>
        {label} <span className="required">*</span>
      </label>
      {input}
      {errors[name] && (
        <p className="field-error" id={`e-${name}`}>
          {errors[name]}
        </p>
      )}
    </div>
  );

  const select = (name, label, values) =>
    field(
      name,
      label,
      <select id={`f-${name}`} value={form[name]} onChange={update(name)} aria-invalid={!!errors[name]}>
        <option value="">Select {label.toLowerCase()}</option>
        {values.map((v) => (
          <option key={v} value={v}>
            {v}
          </option>
        ))}
      </select>
    );

  return (
    <Modal title={isEdit ? "Edit patient" : "Add patient"} onClose={saving ? () => {} : onClose}>
      <form onSubmit={handleSubmit} noValidate>
        {formError && <div className="alert alert-error">{formError}</div>}
        <div className="form-grid">
          {field(
            "name",
            "Name",
            <input
              id="f-name"
              type="text"
              value={form.name}
              onChange={update("name")}
              placeholder="e.g. Asha Patel"
              maxLength={100}
              autoFocus
              aria-invalid={!!errors.name}
            />
          )}
          {field(
            "age",
            "Age",
            <input
              id="f-age"
              type="number"
              inputMode="numeric"
              min="0"
              max="120"
              step="1"
              value={form.age}
              onChange={update("age")}
              placeholder="0 - 120"
              aria-invalid={!!errors.age}
            />
          )}
          {select("gender", "Gender", options.genders)}
          {select("ward", "Ward", options.wards)}
          {select("department", "Department", options.departments)}
          {select("doctor", "Doctor", options.doctors)}
          {field(
            "admission_date",
            "Admission date",
            <input
              id="f-admission_date"
              type="date"
              value={form.admission_date}
              max={todayString()}
              onChange={update("admission_date")}
              aria-invalid={!!errors.admission_date}
            />
          )}
          {isEdit && select("status", "Status", options.statuses)}
        </div>
        <div className="modal-actions">
          <button type="button" className="btn btn-secondary" onClick={onClose} disabled={saving}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? "Saving…" : isEdit ? "Save changes" : "Add patient"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
