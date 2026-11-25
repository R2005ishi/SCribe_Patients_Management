import Modal from "./Modal.jsx";

// "Are you sure?" popup used before deleting (and discharging) a patient.
export default function ConfirmDialog({ title, message, confirmLabel, danger, busy, onConfirm, onCancel }) {
  return (
    <Modal title={title} onClose={busy ? () => {} : onCancel} size="sm">
      <p className="confirm-message">{message}</p>
      <div className="modal-actions">
        <button className="btn btn-secondary" onClick={onCancel} disabled={busy}>
          Cancel
        </button>
        <button className={`btn ${danger ? "btn-danger" : "btn-primary"}`} onClick={onConfirm} disabled={busy}>
          {busy ? "Please wait…" : confirmLabel}
        </button>
      </div>
    </Modal>
  );
}
