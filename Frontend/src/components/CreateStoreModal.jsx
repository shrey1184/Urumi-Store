import { useState } from "react";
import { createStore } from "../api";
import toast from "react-hot-toast";
import { Plus, X, ShoppingBag, Zap } from "lucide-react";

const STORE_TYPES = [
  {
    value: "woocommerce",
    label: "WooCommerce",
    desc: "WordPress + WooCommerce — full-featured ecommerce",
    icon: ShoppingBag,
  },
  {
    value: "medusa",
    label: "MedusaJS",
    desc: "Modern headless commerce — Node.js + PostgreSQL + Next.js",
    icon: Zap,
  },
];

export default function CreateStoreModal({ open, onClose, onCreated }) {
  const [name, setName] = useState("");
  const [storeType, setStoreType] = useState("woocommerce");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const validateName = (val) => {
    if (!/^[a-z0-9][a-z0-9-]*[a-z0-9]$/.test(val) && val.length >= 2) {
      return "Name must be lowercase alphanumeric, may contain hyphens, min 2 chars";
    }
    return "";
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const err = validateName(name);
    if (err) {
      setError(err);
      return;
    }
    setLoading(true);
    setError("");
    try {
      await createStore({ name, store_type: storeType });
      toast.success(`Store "${name}" is being provisioned!`);
      setName("");
      onCreated();
      onClose();
    } catch (err) {
      const msg =
        err.response?.data?.detail || "Failed to create store";
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  if (!open) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>
            <Plus size={20} /> Create New Store
          </h2>
          <button className="btn-icon" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="store-name">Store Name</label>
            <input
              id="store-name"
              type="text"
              placeholder="my-awesome-store"
              value={name}
              onChange={(e) => setName(e.target.value.toLowerCase())}
              disabled={loading}
              autoFocus
              required
              minLength={2}
              maxLength={50}
            />
            <small>
              Lowercase letters, numbers, and hyphens only. This becomes part of
              the store URL.
            </small>
          </div>

          <div className="form-group">
            <label>Store Engine</label>
            <div className="store-types-grid">
              {STORE_TYPES.map((type) => {
                const Icon = type.icon;
                return (
                  <div
                    key={type.value}
                    className={`store-type-card ${
                      storeType === type.value ? "selected" : ""
                    }`}
                    onClick={() => setStoreType(type.value)}
                  >
                    <Icon size={24} />
                    <div>
                      <strong>{type.label}</strong>
                      <span>{type.desc}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {error && <div className="form-error">{error}</div>}

          <div className="modal-actions">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || name.length < 2}
            >
              {loading ? (
                <span className="spinner" />
              ) : (
                <>
                  <Plus size={16} /> Create Store
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
