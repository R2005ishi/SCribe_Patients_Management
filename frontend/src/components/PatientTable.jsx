// Patient list. A normal table on desktop/tablet; CSS turns each row into a
// card on small screens (each cell shows its column name via data-label).

function formatDate(iso) {
  const [y, m, d] = iso.split("-");
  return new Date(Number(y), Number(m) - 1, Number(d)).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export default function PatientTable({ patients, onEdit, onDelete, onDischarge }) {
  return (
    <div className="table-wrap">
      <table className="patient-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Age</th>
            <th>Gender</th>
            <th>Ward</th>
            <th>Department</th>
            <th>Doctor</th>
            <th>Admitted on</th>
            <th>Status</th>
            <th className="actions-col">Actions</th>
          </tr>
        </thead>
        <tbody>
          {patients.map((p) => (
            <tr key={p.id}>
              <td data-label="Name" className="cell-name">{p.name}</td>
              <td data-label="Age">{p.age}</td>
              <td data-label="Gender">{p.gender}</td>
              <td data-label="Ward">{p.ward}</td>
              <td data-label="Department">{p.department}</td>
              <td data-label="Doctor">{p.doctor}</td>
              <td data-label="Admitted on">{formatDate(p.admission_date)}</td>
              <td data-label="Status">
                <span className={`badge ${p.status === "Admitted" ? "badge-admitted" : "badge-discharged"}`}>
                  {p.status}
                </span>
              </td>
              <td className="actions-cell">
                <div className="row-actions">
                  {p.status === "Admitted" && (
                    <button className="btn btn-small btn-success" onClick={() => onDischarge(p)}>
                      Discharge
                    </button>
                  )}
                  <button className="btn btn-small btn-secondary" onClick={() => onEdit(p)}>
                    Edit
                  </button>
                  <button className="btn btn-small btn-danger-outline" onClick={() => onDelete(p)}>
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
