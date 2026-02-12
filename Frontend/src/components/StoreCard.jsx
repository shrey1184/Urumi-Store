import {
  ExternalLink,
  Trash2,
  Clock,
  CheckCircle,
  AlertCircle,
  Loader,
  Settings,
} from "lucide-react";

const STATUS_CONFIG = {
  provisioning: {
    icon: Loader,
    color: "#f59e0b",
    bg: "#fef3c7",
    label: "Provisioning",
    animate: true,
  },
  ready: {
    icon: CheckCircle,
    color: "#10b981",
    bg: "#d1fae5",
    label: "Ready",
  },
  failed: {
    icon: AlertCircle,
    color: "#ef4444",
    bg: "#fee2e2",
    label: "Failed",
  },
  deleting: {
    icon: Loader,
    color: "#6b7280",
    bg: "#f3f4f6",
    label: "Deleting",
    animate: true,
  },
};

export default function StoreCard({ store, onDelete }) {
  const status = STATUS_CONFIG[store.status] || STATUS_CONFIG.failed;
  const StatusIcon = status.icon;

  const formatDate = (dateStr) => {
    const d = new Date(dateStr);
    return d.toLocaleString();
  };

  return (
    <div className={`store-card store-card--${store.status}`}>
      <div className="store-card-header">
        <div className="store-card-title">
          <h3>{store.name}</h3>
          <span className="store-type-badge">{store.store_type}</span>
        </div>
        <div
          className="status-badge"
          style={{ color: status.color, backgroundColor: status.bg }}
        >
          <StatusIcon
            size={14}
            className={status.animate ? "spin" : ""}
          />
          {status.label}
        </div>
      </div>

      <div className="store-card-body">
        <div className="store-info-row">
          <Clock size={14} />
          <span>Created: {formatDate(store.created_at)}</span>
        </div>

        {store.store_url && (
          <div className="store-info-row">
            <ExternalLink size={14} />
            <a href={store.store_url} target="_blank" rel="noopener noreferrer">
              {store.store_url}
            </a>
          </div>
        )}

        {store.admin_url && (
          <div className="store-info-row">
            <Settings size={14} />
            <a href={store.admin_url} target="_blank" rel="noopener noreferrer">
              Admin Panel
            </a>
          </div>
        )}

        {store.error_message && (
          <div className="store-error">
            <AlertCircle size={14} />
            <span>{store.error_message}</span>
          </div>
        )}

        <div className="store-meta">
          <span className="meta-item">
            Namespace: <code>{store.namespace}</code>
          </span>
        </div>
      </div>

      <div className="store-card-footer">
        <button
          className="btn btn-danger btn-sm"
          onClick={() => onDelete(store)}
          disabled={store.status === "deleting"}
        >
          <Trash2 size={14} />
          Delete
        </button>
      </div>
    </div>
  );
}
