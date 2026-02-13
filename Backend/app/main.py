"""
FastAPI application entry point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth_routes import auth_router
from app.config import settings
from app.database import init_db
from app.k8s_client import k8s_client
from app.routes import router

# ──── Logging ────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ──── CORS Origins ────
def _get_cors_origins() -> list[str]:
    """Build CORS origins list: explicit config > FRONTEND_URL > permissive local default."""
    if settings.CORS_ORIGINS:
        return [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    if settings.IN_CLUSTER:
        # Production: only allow the frontend URL (never wildcard with credentials)
        return [settings.FRONTEND_URL] if settings.FRONTEND_URL else []
    # Local dev: permissive
    return ["*"]


# ──── Lifespan ────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s", settings.APP_NAME)

    # Validate critical settings in production
    if settings.IN_CLUSTER:
        if settings.JWT_SECRET_KEY == "your-secret-key-change-in-production":
            raise RuntimeError(
                "FATAL: JWT_SECRET_KEY is set to the insecure default. "
                "Set a strong secret via the JWT_SECRET_KEY environment variable."
            )
        if "sqlite" in settings.DATABASE_URL:
            logger.warning(
                "WARNING: SQLite is not recommended for production. "
                "Set DATABASE_URL to a PostgreSQL connection string."
            )

    # Init database tables
    await init_db()
    # Connect to Kubernetes
    k8s_client.connect()
    logger.info("K8s connected: %s", k8s_client.connected)
    yield
    logger.info("Shutting down %s", settings.APP_NAME)


# ──── App ────
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — configurable per environment
_origins = _get_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True if _origins != ["*"] else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(router, prefix=settings.API_PREFIX)
app.include_router(auth_router, prefix=settings.API_PREFIX)
