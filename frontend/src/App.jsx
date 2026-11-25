import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api.js";
import Filters from "./components/Filters.jsx";
import PatientTable from "./components/PatientTable.jsx";
import PatientForm from "./components/PatientForm.jsx";
import ConfirmDialog from "./components/ConfirmDialog.jsx";

const NO_FILTERS = { search: "", ward: "", department: "", doctor: "", status: "" };

export default function App() {
  const [options, setOptions] = useState(null); // dropdown lists from the backend
  const [patients, setPatients] = useState([]);
  const [filters, setFilters] = useState(NO_FILTERS);
  const [loading, setLoading] = useState(true);
  const [slowServer, setSlowServer] = useState(false); // free hosting "cold start"
  const [loadError, setLoadError] = useState("");

  const [formPatient, setFormPatient] = useState(undefined); // undefined = closed, null = add, object = edit
  const [confirm, setConfirm] = useState(null); // { type: "delete" | "discharge", patient }
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState(null);

  const showToast = useCallback((message, type = "success") => {
    setToast({ message, type, id: Date.now() });
  }, []);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 3500);
    return () => clearTimeout(t);
  }, [toast]);

  // Load the patient list. Search is debounced (waits 300ms after typing stops).
  // latestRequest makes sure an older, slower response never overwrites a newer one.
  const latestRequest = useRef(0);
  const loadPatients = useCallback(async (currentFilters) => {
    const requestId = ++latestRequest.current;
    setLoading(true);
    setLoadError("");
    const slowTimer = setTimeout(() => setSlowServer(true), 3000);
    try {
      const data = await api.listPatients(currentFilters);
      if (requestId === latestRequest.current) setPatients(data);
    } catch (err) {
      if (requestId === latestRequest.current) setLoadError(err.message);
    } finally {
      clearTimeout(slowTimer);
      if (requestId === latestRequest.current) {
        setSlowServer(false);
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    const t = setTimeout(() => loadPatients(filters), 300);
    return () => clearTimeout(t);
  }, [filters, loadPatients]);

  // Load dropdown options once.
  const loadOptions = useCallback(() => {
    api
      .getOptions()
      .then(setOptions)
      .catch((err) => setLoadError(err.message));
  }, []);
  useEffect(loadOptions, [loadOptions]);

  const retry = () => {
    if (!options) loadOptions();
    loadPatients(filters);
  };

  // ----- Actions -----

  async function handleSave(payload) {
    if (formPatient) {
      await api.updatePatient(formPatient.id, payload);
      showToast(`${payload.name} updated`);
    } else {
      await api.createPatient(payload);
      showToast(`${payload.name} added`);
    }
    setFormPatient(undefined);
    loadPatients(filters);
  }

  async function handleConfirm() {
    const { type, patient } = confirm;
    setBusy(true);
    try {
      if (type === "delete") {
        await api.deletePatient(patient.id);
        showToast(`${patient.name} deleted`);
      } else {
        await api.dischargePatient(patient.id);
        showToast(`${patient.name} marked as discharged`);
      }
      setConfirm(null);
      loadPatients(filters);
    } catch (err) {
      showToast(err.message, "error");
      setConfirm(null);
    } finally {
      setBusy(false);
    }
  }

  const admittedCount = patients.filter((p) => p.status === "Admitted").length;
  const hasFilters = Object.values(filters).some((v) => v);

  return (
    <div className="app">
      <header className="app-header">
        <div className="container header-inner">
          <div className="brand">
            <div className="logo" aria-hidden="true">+</div>
            <div>
              <h1>Patient Admissions</h1>
              <p className="subtitle">Manage admitted patients across wards</p>
            </div>
          </div>
          <button className="btn btn-primary" onClick={() => setFormPatient(null)} disabled={!options}>
            + Add patient
          </button>
        </div>
      </header>

      <main className="container">
        {options && (
          <Filters
            filters={filters}
            options={options}
            onChange={setFilters}
            onClear={() => setFilters(NO_FILTERS)}
          />
        )}

        <div className="list-header">
          <h2>
            {hasFilters ? "Matching patients" : "All patients"}{" "}
            <span className="count">{patients.length}</span>
          </h2>
          <span className="muted">{admittedCount} currently admitted</span>
        </div>

        {loadError ? (
          <div className="state-box">
            <p className="alert alert-error">{loadError}</p>
            <button className="btn btn-secondary" onClick={retry}>
              Try again
            </button>
          </div>
        ) : loading && patients.length === 0 ? (
          <div className="state-box">
            <div className="spinner" aria-hidden="true" />
            <p>Loading patients…</p>
            {slowServer && (
              <p className="muted">The server is waking up (free hosting). This can take up to a minute.</p>
            )}
          </div>
        ) : patients.length === 0 ? (
          <div className="state-box">
            <p className="empty-title">{hasFilters ? "No patients match your filters" : "No patients yet"}</p>
            <p className="muted">
              {hasFilters ? "Try changing or clearing the filters." : "Click “Add patient” to admit the first one."}
            </p>
          </div>
        ) : (
          <div className={loading ? "is-refreshing" : ""}>
            <PatientTable
              patients={patients}
              onEdit={(p) => setFormPatient(p)}
              onDelete={(p) => setConfirm({ type: "delete", patient: p })}
              onDischarge={(p) => setConfirm({ type: "discharge", patient: p })}
            />
          </div>
        )}
      </main>

      {formPatient !== undefined && options && (
        <PatientForm
          patient={formPatient}
          options={options}
          onSubmit={handleSave}
          onClose={() => setFormPatient(undefined)}
        />
      )}

      {confirm && (
        <ConfirmDialog
          title={confirm.type === "delete" ? "Delete patient?" : "Discharge patient?"}
          message={
            confirm.type === "delete"
              ? `This will permanently delete ${confirm.patient.name}'s record. This cannot be undone.`
              : `Mark ${confirm.patient.name} as discharged?`
          }
          confirmLabel={confirm.type === "delete" ? "Delete" : "Discharge"}
          danger={confirm.type === "delete"}
          busy={busy}
          onConfirm={handleConfirm}
          onCancel={() => setConfirm(null)}
        />
      )}

      {toast && (
        <div key={toast.id} className={`toast toast-${toast.type}`} role="status">
          {toast.message}
        </div>
      )}
    </div>
  );
}
