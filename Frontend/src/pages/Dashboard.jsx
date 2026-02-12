import { useEffect, useState, useCallback } from "react";
import { getStores, deleteStore } from "../api";
import StoreCard from "../components/StoreCard";
import CreateStoreModal from "../components/CreateStoreModal";
import StatusBar from "../components/StatusBar";
import toast from "react-hot-toast";
import {
  Plus,
  RefreshCw,
  Store,
  LayoutDashboard,
} from "lucide-react";

export default function Dashboard() {
  const [stores, setStores] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const fetchStores = useCallback(async () => {
    try {
      const res = await getStores();
      setStores(res.data.stores);
    } catch (err) {
      toast.error("Failed to fetch stores");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // Initial fetch + polling every 5 seconds
  useEffect(() => {
    fetchStores();
    const interval = setInterval(fetchStores, 5000);
    return () => clearInterval(interval);
  }, [fetchStores]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchStores();
  };

  const handleDelete = async (store) => {
    if (
      !window.confirm(
        `Are you sure you want to delete store "${store.name}"? All resources will be cleaned up.`
      )
    )
      return;

    try {
      await deleteStore(store.id);
      toast.success(`Store "${store.name}" deletion initiated`);
      fetchStores();
    } catch (err) {
      const msg = err.response?.data?.detail || "Failed to delete store";
      toast.error(msg);
    }
  };

  const provisioningCount = stores.filter(
    (s) => s.status === "provisioning"
  ).length;
  const readyCount = stores.filter((s) => s.status === "ready").length;
  const failedCount = stores.filter((s) => s.status === "failed").length;

  return (
    <div className="dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div className="header-left">
          <LayoutDashboard size={28} />
          <h1>Store Provisioning Platform</h1>
        </div>
        <div className="header-right">
          <button
            className="btn btn-secondary"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw size={16} className={refreshing ? "spin" : ""} />
            Refresh
          </button>
          <button
            className="btn btn-primary"
            onClick={() => setModalOpen(true)}
          >
            <Plus size={16} />
            Create Store
          </button>
        </div>
      </header>

      {/* Status Bar */}
      <StatusBar />

      {/* Stats */}
      <div className="stats-row">
        <div className="stat-card">
          <Store size={20} />
          <div>
            <span className="stat-number">{stores.length}</span>
            <span className="stat-label">Total Stores</span>
          </div>
        </div>
        <div className="stat-card stat-ready">
          <div>
            <span className="stat-number">{readyCount}</span>
            <span className="stat-label">Ready</span>
          </div>
        </div>
        <div className="stat-card stat-provisioning">
          <div>
            <span className="stat-number">{provisioningCount}</span>
            <span className="stat-label">Provisioning</span>
          </div>
        </div>
        <div className="stat-card stat-failed">
          <div>
            <span className="stat-number">{failedCount}</span>
            <span className="stat-label">Failed</span>
          </div>
        </div>
      </div>

      {/* Store Grid */}
      {loading ? (
        <div className="loading-state">
          <div className="spinner-lg" />
          <p>Loading stores...</p>
        </div>
      ) : stores.length === 0 ? (
        <div className="empty-state">
          <Store size={48} />
          <h2>No stores yet</h2>
          <p>Create your first ecommerce store to get started.</p>
          <button
            className="btn btn-primary"
            onClick={() => setModalOpen(true)}
          >
            <Plus size={16} />
            Create Your First Store
          </button>
        </div>
      ) : (
        <div className="store-grid">
          {stores.map((store) => (
            <StoreCard key={store.id} store={store} onDelete={handleDelete} />
          ))}
        </div>
      )}

      {/* Create Store Modal */}
      <CreateStoreModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreated={fetchStores}
      />
    </div>
  );
}
