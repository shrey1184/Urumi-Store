import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Store Provisioning Platform"
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    API_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./stores.db")

    # Kubernetes
    KUBECONFIG: str | None = os.getenv("KUBECONFIG") or None
    IN_CLUSTER: bool = os.getenv("IN_CLUSTER", "false").lower() == "true"

    # Helm
    HELM_BINARY: str = os.getenv("HELM_BINARY", "helm")
    STORE_CHART_PATH: str = os.getenv(
        "STORE_CHART_PATH",
        os.path.join(os.path.dirname(__file__), "..", "..", "helm"),
    )

    # Ingress
    BASE_DOMAIN: str = os.getenv("BASE_DOMAIN", "local.store.dev")
    INGRESS_CLASS: str = os.getenv("INGRESS_CLASS", "nginx")

    # Guardrails
    MAX_STORES: int = int(os.getenv("MAX_STORES", "100"))  # Global limit
    MAX_STORES_PER_USER: int = int(os.getenv("MAX_STORES_PER_USER", "5"))  # Per-user limit
    PROVISION_TIMEOUT_SECONDS: int = int(os.getenv("PROVISION_TIMEOUT_SECONDS", "600"))
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))

    # Store namespace prefix
    NAMESPACE_PREFIX: str = os.getenv("NAMESPACE_PREFIX", "store-")

    # Authentication & JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080")
    )  # 7 days

    # OAuth - Google
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_AUTHORIZATION_ENDPOINT: str = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_ENDPOINT: str = "https://oauth2.googleapis.com/token"
    GOOGLE_USERINFO_ENDPOINT: str = "https://www.googleapis.com/oauth2/v1/userinfo"
    OAUTH_REDIRECT_URI: str = os.getenv(
        "OAUTH_REDIRECT_URI", "http://localhost:8000/api/v1/auth/callback/google"
    )

    # Frontend URL for redirects
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # CORS — comma-separated origins (defaults to FRONTEND_URL for production safety)
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "")

    # SMTP / Email (Gmail App Password)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")  # your-gmail@gmail.com
    SMTP_APP_PASSWORD: str = os.getenv("SMTP_APP_PASSWORD", "")  # 16-char Google App Password

    class Config:
        env_file = ".env"


settings = Settings()
