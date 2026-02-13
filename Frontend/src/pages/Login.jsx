import { useState, useEffect } from "react";
import { LogIn, Shield, Store as StoreIcon } from "lucide-react";
import API_BASE from "../config";
import toast from "react-hot-toast";

export default function Login() {
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Check if already logged in and verify token is valid
    const token = localStorage.getItem("auth_token");
    if (token) {
      // Verify token is valid before redirecting
      fetch(`${API_BASE}/auth/me`, {
        headers: { Authorization: `Bearer ${token}` }
      })
        .then(res => {
          if (res.ok) {
            window.location.href = "/dashboard";
          } else {
            // Invalid token, remove it
            localStorage.removeItem("auth_token");
          }
        })
        .catch(() => {
          // Invalid token, remove it
          localStorage.removeItem("auth_token");
        });
    }
  }, []);

  const handleGoogleLogin = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/auth/login/google`);
      const data = await response.json();

      if (data.authorization_url) {
        // Redirect to Google OAuth
        window.location.href = data.authorization_url;
      } else {
        toast.error("Failed to initiate login");
      }
    } catch (error) {
      console.error("Login error:", error);
      toast.error("Failed to initiate login");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      {/* Background Geometric Patterns */}
      <div className="geometric-bg">
        <div className="shape shape-1"></div>
        <div className="shape shape-2"></div>
        <div className="shape shape-3"></div>
        <div className="shape shape-4"></div>
      </div>

      {/* Login Card */}
      <div className="login-card">
        <div className="login-header">
          <div className="login-icon">
            <Shield size={48} />
          </div>
          <h1>Store Provisioning Platform</h1>
          <p>Deploy WooCommerce and MedusaJS stores in seconds</p>
        </div>

        <div className="login-features">
          <div className="feature">
            <StoreIcon size={20} />
            <span>Multi-tenant store isolation</span>
          </div>
          <div className="feature">
            <Shield size={20} />
            <span>Kubernetes-native deployment</span>
          </div>
          <div className="feature">
            <LogIn size={20} />
            <span>Secure OAuth authentication</span>
          </div>
        </div>

        <button
          className="btn btn-google"
          onClick={handleGoogleLogin}
          disabled={loading}
        >
          <svg viewBox="0 0 24 24" width="20" height="20">
            <path
              fill="currentColor"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="currentColor"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="currentColor"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
            />
            <path
              fill="currentColor"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            />
          </svg>
          {loading ? "Redirecting..." : "Continue with Google"}
        </button>

        <div className="login-footer">
          <p>
            By continuing, you agree to our Terms of Service and Privacy Policy
          </p>
        </div>
      </div>

      <style jsx>{`
        .login-container {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 2rem;
          position: relative;
          overflow: hidden;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }

        .geometric-bg {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          overflow: hidden;
          opacity: 0.1;
        }

        .shape {
          position: absolute;
          background: white;
        }

        .shape-1 {
          width: 300px;
          height: 300px;
          border-radius: 50%;
          top: -150px;
          left: -150px;
        }

        .shape-2 {
          width: 200px;
          height: 200px;
          transform: rotate(45deg);
          bottom: -100px;
          right: -100px;
        }

        .shape-3 {
          width: 150px;
          height: 150px;
          clip-path: polygon(50% 0%, 0% 100%, 100% 100%);
          top: 50%;
          right: 10%;
        }

        .shape-4 {
          width: 250px;
          height: 250px;
          border-radius: 30% 70% 70% 30% / 30% 30% 70% 70%;
          bottom: 20%;
          left: 5%;
        }

        .login-card {
          background: white;
          border-radius: 24px;
          padding: 3rem;
          max-width: 480px;
          width: 100%;
          box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
          position: relative;
          z-index: 1;
        }

        .login-header {
          text-align: center;
          margin-bottom: 2.5rem;
        }

        .login-icon {
          display: inline-flex;
          padding: 1rem;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border-radius: 16px;
          color: white;
          margin-bottom: 1.5rem;
        }

        .login-header h1 {
          font-size: 1.75rem;
          font-weight: 700;
          margin: 0 0 0.5rem 0;
          color: #1a202c;
        }

        .login-header p {
          color: #718096;
          margin: 0;
          font-size: 0.95rem;
        }

        .login-features {
          display: flex;
          flex-direction: column;
          gap: 1rem;
          margin-bottom: 2rem;
          padding: 1.5rem;
          background: #f7fafc;
          border-radius: 12px;
        }

        .feature {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          color: #4a5568;
          font-size: 0.9rem;
        }

        .feature svg {
          color: #667eea;
          flex-shrink: 0;
        }

        .btn-google {
          width: 100%;
          padding: 1rem 1.5rem;
          background: #4285f4;
          color: white;
          border: none;
          border-radius: 12px;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.75rem;
          transition: all 0.2s;
          margin-bottom: 1.5rem;
        }

        .btn-google:hover:not(:disabled) {
          background: #357ae8;
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(66, 133, 244, 0.3);
        }

        .btn-google:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .btn-google svg {
          background: white;
          border-radius: 4px;
          padding: 2px;
        }

        .login-footer {
          text-align: center;
          font-size: 0.8rem;
          color: #a0aec0;
        }

        .login-footer p {
          margin: 0;
          line-height: 1.5;
        }

        @media (max-width: 640px) {
          .login-card {
            padding: 2rem;
          }

          .login-header h1 {
            font-size: 1.5rem;
          }
        }
      `}</style>
    </div>
  );
}
