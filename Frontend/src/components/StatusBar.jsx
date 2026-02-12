import { useEffect, useState } from "react";
import { healthCheck } from "../api";
import { Activity, Server, Wifi, WifiOff } from "lucide-react";

export default function StatusBar() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    const check = async () => {
      try {
        const res = await healthCheck();
        setHealth(res.data);
      } catch {
        setHealth(null);
      }
    };
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="status-bar">
      <div className="status-bar-item">
        <Server size={14} />
        <span>
          API:{" "}
          {health ? (
            <span className="text-green">Connected</span>
          ) : (
            <span className="text-red">Disconnected</span>
          )}
        </span>
      </div>
      <div className="status-bar-item">
        {health?.kubernetes_connected ? (
          <>
            <Wifi size={14} />
            <span className="text-green">K8s Connected</span>
          </>
        ) : (
          <>
            <WifiOff size={14} />
            <span className="text-red">K8s Disconnected</span>
          </>
        )}
      </div>
      {health && (
        <div className="status-bar-item">
          <Activity size={14} />
          <span>v{health.version}</span>
        </div>
      )}
    </div>
  );
}
