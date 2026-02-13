import { useState, useEffect } from "react";
import { LogIn, Shield, Store as StoreIcon, Circle, Square, Triangle } from "lucide-react";
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
      {/* Bauhaus Geometric Background */}
      <div className="bauhaus-bg">
        <div className="bauhaus-circle bauhaus-circle-1"></div>
        <div className="bauhaus-circle bauhaus-circle-2"></div>
        <div className="bauhaus-square bauhaus-square-1"></div>
        <div className="bauhaus-square bauhaus-square-2"></div>
        <div className="bauhaus-triangle bauhaus-triangle-1"></div>
        <div className="bauhaus-line bauhaus-line-1"></div>
        <div className="bauhaus-line bauhaus-line-2"></div>
        <div className="bauhaus-line bauhaus-line-3"></div>
      </div>

      {/* Login Card */}
      <div className="login-card">
        <div className="login-header">
          <div className="bauhaus-logo">
            <div className="bauhaus-logo-shapes">
              <div className="logo-circle"></div>
              <div className="logo-square"></div>
              <div className="logo-triangle"></div>
            </div>
          </div>
          <h1>STORE PLATFORM</h1>
          <div className="bauhaus-divider"></div>
          <p>Deploy WooCommerce and MedusaJS stores in seconds</p>
        </div>

        <div className="login-features">
          <div className="feature">
            <div className="feature-icon feature-icon-blue">
              <StoreIcon size={18} strokeWidth={2.5} />
            </div>
            <span>Multi-tenant isolation</span>
          </div>
          <div className="feature">
            <div className="feature-icon feature-icon-red">
              <Shield size={18} strokeWidth={2.5} />
            </div>
            <span>Kubernetes-native</span>
          </div>
          <div className="feature">
            <div className="feature-icon feature-icon-yellow">
              <LogIn size={18} strokeWidth={2.5} />
            </div>
            <span>Secure OAuth</span>
          </div>
        </div>

        <button
          className="btn btn-google"
          onClick={handleGoogleLogin}
          disabled={loading}
        >
          <svg viewBox="0 0 24 24" width="24" height="24" className="google-icon">
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
            />
          </svg>
          {loading ? "REDIRECTING..." : "CONTINUE WITH GOOGLE"}
        </button>

        <div className="login-footer">
          <div className="footer-divider"></div>
          <p>
            By continuing, you agree to our Terms & Privacy Policy
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
          background: #f5f5f0;
        }

        /* Bauhaus Background Shapes */
        .bauhaus-bg {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          overflow: hidden;
        }

        .bauhaus-circle {
          position: absolute;
          border-radius: 50%;
          opacity: 0.8;
        }

        .bauhaus-circle-1 {
          width: 400px;
          height: 400px;
          background: #0066cc;
          top: -200px;
          right: -100px;
        }

        .bauhaus-circle-2 {
          width: 200px;
          height: 200px;
          background: #ffd500;
          bottom: 10%;
          left: 5%;
        }

        .bauhaus-square {
          position: absolute;
          opacity: 0.8;
        }

        .bauhaus-square-1 {
          width: 300px;
          height: 300px;
          background: #dd0000;
          bottom: -150px;
          right: 10%;
          transform: rotate(15deg);
        }

        .bauhaus-square-2 {
          width: 150px;
          height: 150px;
          background: #000000;
          top: 20%;
          left: -50px;
          transform: rotate(-20deg);
        }

        .bauhaus-triangle {
          position: absolute;
          width: 0;
          height: 0;
          opacity: 0.8;
        }

        .bauhaus-triangle-1 {
          border-left: 150px solid transparent;
          border-right: 150px solid transparent;
          border-bottom: 260px solid #0066cc;
          top: 15%;
          right: 15%;
          transform: rotate(30deg);
        }

        .bauhaus-line {
          position: absolute;
          opacity: 0.6;
        }

        .bauhaus-line-1 {
          width: 4px;
          height: 400px;
          background: #000000;
          top: 0;
          left: 20%;
          transform: rotate(15deg);
        }

        .bauhaus-line-2 {
          width: 600px;
          height: 4px;
          background: #dd0000;
          bottom: 30%;
          left: -100px;
          transform: rotate(-20deg);
        }

        .bauhaus-line-3 {
          width: 4px;
          height: 300px;
          background: #ffd500;
          bottom: 0;
          right: 25%;
          transform: rotate(-10deg);
        }

        .login-card {
          background: #ffffff;
          border: 4px solid #000000;
          padding: 3rem;
          max-width: 480px;
          width: 100%;
          box-shadow: 12px 12px 0 rgba(0, 0, 0, 0.8);
          position: relative;
          z-index: 1;
        }

        .login-header {
          text-align: center;
          margin-bottom: 2.5rem;
        }

        /* Bauhaus Logo */
        .bauhaus-logo {
          margin-bottom: 1.5rem;
        }

        .bauhaus-logo-shapes {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          margin-bottom: 1rem;
        }

        .logo-circle {
          width: 50px;
          height: 50px;
          border-radius: 50%;
          background: #0066cc;
        }

        .logo-square {
          width: 50px;
          height: 50px;
          background: #dd0000;
        }

        .logo-triangle {
          width: 0;
          height: 0;
          border-left: 25px solid transparent;
          border-right: 25px solid transparent;
          border-bottom: 43px solid #ffd500;
        }

        .login-header h1 {
          font-size: 2rem;
          font-weight: 900;
          margin: 0 0 1rem 0;
          color: #000000;
          letter-spacing: 0.05em;
          text-transform: uppercase;
          font-family: 'Helvetica Neue', Arial, sans-serif;
        }

        .bauhaus-divider {
          width: 80px;
          height: 4px;
          background: #dd0000;
          margin: 1rem auto;
        }

        .login-header p {
          color: #333333;
          margin: 0;
          font-size: 0.95rem;
          font-weight: 500;
          line-height: 1.6;
        }

        .login-features {
          display: flex;
          flex-direction: column;
          gap: 1rem;
          margin-bottom: 2rem;
          padding: 1.5rem;
          background: #f5f5f0;
          border: 3px solid #000000;
        }

        .feature {
          display: flex;
          align-items: center;
          gap: 1rem;
          color: #000000;
          font-size: 0.9rem;
          font-weight: 600;
        }

        .feature-icon {
          width: 36px;
          height: 36px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          border: 2px solid #000000;
        }

        .feature-icon-blue {
          background: #0066cc;
          color: #ffffff;
        }

        .feature-icon-red {
          background: #dd0000;
          color: #ffffff;
          border-radius: 50%;
        }

        .feature-icon-yellow {
          background: #ffd500;
          color: #000000;
        }

        .btn-google {
          width: 100%;
          padding: 1rem 1.5rem;
          background: #ffffff;
          color: #000000;
          border: 3px solid #000000;
          font-size: 1rem;
          font-weight: 900;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.75rem;
          transition: all 0.15s;
          margin-bottom: 1.5rem;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          box-shadow: 6px 6px 0 rgba(0, 0, 0, 1);
          position: relative;
          font-family: 'Helvetica Neue', Arial, sans-serif;
        }

        .btn-google:hover:not(:disabled) {
          transform: translate(3px, 3px);
          box-shadow: 3px 3px 0 rgba(0, 0, 0, 1);
        }

        .btn-google:active:not(:disabled) {
          transform: translate(6px, 6px);
          box-shadow: 0 0 0 rgba(0, 0, 0, 1);
        }

        .btn-google:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .google-icon {
          flex-shrink: 0;
        }

        .login-footer {
          text-align: center;
        }

        .footer-divider {
          width: 100%;
          height: 2px;
          background: #000000;
          margin-bottom: 1rem;
        }

        .login-footer p {
          margin: 0;
          line-height: 1.5;
          font-size: 0.75rem;
          color: #666666;
          font-weight: 500;
        }

        @media (max-width: 640px) {
          .login-card {
            padding: 2rem;
            box-shadow: 8px 8px 0 rgba(0, 0, 0, 0.8);
          }

          .login-header h1 {
            font-size: 1.5rem;
          }

          .bauhaus-circle-1 {
            width: 300px;
            height: 300px;
          }

          .bauhaus-square-1 {
            width: 200px;
            height: 200px;
          }

          .btn-google {
            box-shadow: 4px 4px 0 rgba(0, 0, 0, 1);
          }
        }
      `}</style>
    </div>
  );
}
