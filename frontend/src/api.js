// All calls to the backend live here.
const BASE_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

// Error thrown for any failed request. `fieldErrors` holds the backend's
// per-field validation messages, e.g. { age: "Age must be between 0 and 120" }.
export class ApiError extends Error {
  constructor(message, fieldErrors = {}) {
    super(message);
    this.fieldErrors = fieldErrors;
  }
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    throw new ApiError("Cannot reach the server. Please check your connection and try again.");
  }

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    const message = typeof data?.detail === "string" ? data.detail : `Request failed (${response.status})`;
    throw new ApiError(message, data?.errors || {});
  }
  return data;
}

export const api = {
  getOptions: () => request("/api/options"),

  listPatients: (filters) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value && String(value).trim()) params.append(key, String(value).trim());
    });
    const qs = params.toString();
    return request(`/api/patients${qs ? `?${qs}` : ""}`);
  },

  createPatient: (patient) =>
    request("/api/patients", { method: "POST", body: JSON.stringify(patient) }),

  updatePatient: (id, patient) =>
    request(`/api/patients/${id}`, { method: "PUT", body: JSON.stringify(patient) }),

  dischargePatient: (id) => request(`/api/patients/${id}/discharge`, { method: "PATCH" }),

  deletePatient: (id) => request(`/api/patients/${id}`, { method: "DELETE" }),
};
