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
        os.path.join(os.path.dirname(__file__), "..", "..", "helm", "store-chart"),
    )

    # Ingress
    BASE_DOMAIN: str = os.getenv("BASE_DOMAIN", "local.store.dev")
    INGRESS_CLASS: str = os.getenv("INGRESS_CLASS", "nginx")

    # Guardrails
    MAX_STORES: int = int(os.getenv("MAX_STORES", "10"))
    PROVISION_TIMEOUT_SECONDS: int = int(os.getenv("PROVISION_TIMEOUT_SECONDS", "600"))
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))

    # Store namespace prefix
    NAMESPACE_PREFIX: str = os.getenv("NAMESPACE_PREFIX", "store-")

    class Config:
        env_file = ".env"


settings = Settings()
