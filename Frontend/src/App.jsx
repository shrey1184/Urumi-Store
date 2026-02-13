import { Toaster } from "react-hot-toast";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import AuthCallback from "./pages/AuthCallback";
import "./App.css";

// Protected Route Component
function ProtectedRoute({ children }) {
  const token = localStorage.getItem("auth_token");
  
  if (!token) {
    return <Navigate to="/" replace />;
  }
  
  return children;
}

function App() {
  return (
    <BrowserRouter>
      {/* Bauhaus Geometric Background */}
      <div className="geometric-bg">
        <div className="shape-1"></div>
        <div className="shape-2"></div>
        <div className="shape-3"></div>
        <div className="shape-4"></div>
        <div className="shape-5"></div>
        <div className="shape-6"></div>
        <div className="shape-7"></div>
        <div className="shape-8"></div>
        <div className="side-block-left"></div>
        <div className="side-block-right"></div>
      </div>
      
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            borderRadius: "0px",
            background: "#1a1a1a",
            color: "#F5F5F5",
            fontSize: "14px",
            fontWeight: "600",
            border: "3px solid #0066CC",
            boxShadow: "4px 4px 0 rgba(0,0,0,0.2)",
          },
        }}
      />
      
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
