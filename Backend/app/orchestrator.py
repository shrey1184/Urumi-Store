"""
Store provisioning orchestrator — handles the full lifecycle of creating/deleting stores.
Runs provisioning in background tasks for non-blocking API responses.
"""

import asyncio
import base64
import logging
import os
import secrets
import string
from datetime import UTC, datetime

from sqlalchemy import select

from app.config import settings
from app.database import async_session
from app.helm_client import helm_client
from app.k8s_client import k8s_client
from app.models import Store, StoreStatus, StoreType

logger = logging.getLogger(__name__)

# In-memory lock to prevent duplicate provisioning of the same store
_provisioning_locks: dict[str, asyncio.Lock] = {}


def _generate_password(length: int = 16) -> str:
    """Generate a secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _get_namespace(store_name: str) -> str:
    return f"{settings.NAMESPACE_PREFIX}{store_name}"


def _get_store_url(store_name: str) -> str:
    return f"https://{store_name}.{settings.BASE_DOMAIN}"


def _get_admin_url(store_name: str, store_type: StoreType) -> str:
    return f"https://{store_name}.{settings.BASE_DOMAIN}/wp-admin"


class StoreOrchestrator:
    """Handles provisioning and teardown of stores."""

    async def create_store(self, store: Store) -> None:
        """Background task: provision a store end-to-end."""
        lock = _provisioning_locks.setdefault(store.id, asyncio.Lock())

        if lock.locked():
            logger.warning("Store %s is already being provisioned (idempotent skip)", store.id)
            return

        async with lock:
            try:
                await self._provision(store)
            except Exception as e:
                logger.exception("Failed to provision store %s: %s", store.name, e)
                await self._update_store_status(store.id, StoreStatus.FAILED, error=str(e))
            finally:
                _provisioning_locks.pop(store.id, None)

    async def _provision(self, store: Store) -> None:
        """Core provisioning logic."""
        namespace = store.namespace

        # Step 1: Create namespace
        logger.info("[%s] Creating namespace %s", store.name, namespace)
        k8s_client.create_namespace(
            namespace,
            labels={
                "managed-by": "store-platform",
                "store-name": store.name,
                "store-type": store.store_type.value,
            },
        )

        # Step 2: Apply ResourceQuota & LimitRange for isolation
        logger.info("[%s] Applying resource guardrails", store.name)
        k8s_client.apply_resource_quota(namespace)
        k8s_client.apply_limit_range(namespace)

        # Step 2.5: Create TLS secret for HTTPS
        logger.info("[%s] Creating TLS secret", store.name)
        self._create_tls_secret(namespace)

        # Step 3: Helm install the store chart
        logger.info("[%s] Installing Helm chart", store.name)
        chart_path = self._get_chart_path(store.store_type)

        wp_password = _generate_password()
        db_password = _generate_password()

        helm_values = self._build_helm_values(store, wp_password, db_password)

        success, output = await helm_client.install(
            release_name=store.name,
            chart_path=chart_path,
            namespace=namespace,
            values=helm_values,
            timeout=f"{settings.PROVISION_TIMEOUT_SECONDS}s",
            wait=True,
        )

        if not success:
            raise RuntimeError(f"Helm install failed: {output}")

        # Step 4: Update store record with URLs
        store_url = _get_store_url(store.name)
        admin_url = _get_admin_url(store.name, store.store_type)

        await self._update_store_status(
            store.id,
            StoreStatus.READY,
            store_url=store_url,
            admin_url=admin_url,
            metadata_json={
                "admin_user": "admin",
                "admin_password": wp_password,
                "db_password": db_password,
                "helm_release": store.name,
            },
        )
        logger.info("[%s] Store provisioned successfully at %s", store.name, store_url)

    async def delete_store(self, store: Store) -> None:
        """Background task: tear down a store cleanly."""
        try:
            await self._update_store_status(store.id, StoreStatus.DELETING)

            # Step 1: Uninstall Helm release
            logger.info("[%s] Uninstalling Helm release", store.name)
            success, output = await helm_client.uninstall(store.name, store.namespace)
            if not success:
                logger.warning("[%s] Helm uninstall warning: %s", store.name, output)

            # Step 2: Delete namespace (cleans up all remaining resources)
            logger.info("[%s] Deleting namespace %s", store.name, store.namespace)
            k8s_client.delete_namespace(store.namespace)

            # Step 3: Remove from DB
            async with async_session() as session:
                result = await session.execute(select(Store).where(Store.id == store.id))
                db_store = result.scalar_one_or_none()
                if db_store:
                    await session.delete(db_store)
                    await session.commit()

            logger.info("[%s] Store deleted successfully", store.name)

        except Exception as e:
            logger.exception("Failed to delete store %s: %s", store.name, e)
            await self._update_store_status(
                store.id, StoreStatus.FAILED, error=f"Delete failed: {e}"
            )

    def _get_chart_path(self, store_type: StoreType) -> str:
        """Resolve the Helm chart path for a store type."""
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "helm"))
        return os.path.join(base, "woocommerce")

    def _create_tls_secret(self, namespace: str):
        """Copy the TLS certificate to the namespace."""
        # Read the cert and key from /tmp (created during setup)
        cert_path = "/tmp/tls.crt"
        key_path = "/tmp/tls.key"

        if not os.path.exists(cert_path) or not os.path.exists(key_path):
            logger.warning("TLS cert/key not found, skipping HTTPS setup")
            return

        with open(cert_path, "rb") as f:
            cert_data = base64.b64encode(f.read())
        with open(key_path, "rb") as f:
            key_data = base64.b64encode(f.read())

        k8s_client.create_tls_secret(namespace, "local-store-tls", cert_data, key_data)

    def _build_helm_values(self, store: Store, wp_password: str, db_password: str) -> dict:
        """Build Helm --set values for store provisioning."""
        values = {
            "storeName": store.name,
            "baseDomain": settings.BASE_DOMAIN,
            "ingress.className": settings.INGRESS_CLASS,
            "ingress.host": f"{store.name}.{settings.BASE_DOMAIN}",
            "wordpress.adminUser": "admin",
            "wordpress.adminPassword": wp_password,
            "wordpress.adminEmail": f"admin@{store.name}.{settings.BASE_DOMAIN}",
            "mysql.rootPassword": db_password,
            "mysql.database": "wordpress",
            "mysql.user": "wordpress",
            "mysql.password": db_password,
        }
        return values

    async def _update_store_status(
        self,
        store_id: str,
        status: StoreStatus,
        error: str | None = None,
        store_url: str | None = None,
        admin_url: str | None = None,
        metadata_json: dict | None = None,
    ):
        """Update store status in the DB."""
        async with async_session() as session:
            result = await session.execute(select(Store).where(Store.id == store_id))
            store = result.scalar_one_or_none()
            if store:
                store.status = status
                store.updated_at = datetime.now(UTC)
                if error:
                    store.error_message = error
                if store_url:
                    store.store_url = store_url
                if admin_url:
                    store.admin_url = admin_url
                if metadata_json:
                    store.metadata_json = metadata_json
                await session.commit()


# Global singleton
orchestrator = StoreOrchestrator()
