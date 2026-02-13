import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";

export default function AuthCallback() {
  const navigate = useNavigate();
  const hasRun = useRef(false);

  useEffect(() => {
    // Prevent double execution
    if (hasRun.current) return;
    hasRun.current = true;

    // Extract token from URL
    const params = new URLSearchParams(window.location.search);
    const token = params.get("token");

    if (token) {
      // Store token in localStorage
      localStorage.setItem("auth_token", token);
      toast.success("Successfully logged in!");
      
      // Redirect to dashboard
      setTimeout(() => navigate("/dashboard"), 500);
    } else {
      toast.error("Authentication failed");
      setTimeout(() => navigate("/"), 500);
    }
  }, [navigate]);

  return (
    <div style={{ 
      display: "flex", 
      justifyContent: "center", 
      alignItems: "center", 
      height: "100vh",
      flexDirection: "column",
      gap: "1rem"
    }}>
      <div className="spinner"></div>
      <p>Completing authentication...</p>
    </div>
  );
}
