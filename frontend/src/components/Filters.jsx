// Search box + Ward / Department / Doctor / Status filters.
export default function Filters({ filters, options, onChange, onClear }) {
  const set = (field) => (e) => onChange({ ...filters, [field]: e.target.value });
  const hasFilters = Object.values(filters).some((v) => v);

  const select = (field, label, values) => (
    <label className="filter-field">
      <span>{label}</span>
      <select value={filters[field]} onChange={set(field)}>
        <option value="">All</option>
        {values.map((v) => (
          <option key={v} value={v}>
            {v}
          </option>
        ))}
      </select>
    </label>
  );

  return (
    <section className="filters" aria-label="Search and filters">
      <label className="filter-field search-field">
        <span>Search by name</span>
        <input
          type="search"
          placeholder="Type a patient name…"
          value={filters.search}
          onChange={set("search")}
        />
      </label>
      {select("ward", "Ward", options.wards)}
      {select("department", "Department", options.departments)}
      {select("doctor", "Doctor", options.doctors)}
      {select("status", "Status", options.statuses)}
      <button className="btn btn-secondary clear-btn" onClick={onClear} disabled={!hasFilters}>
        Clear
      </button>
    </section>
  );
}
