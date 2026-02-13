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
import subprocess
from datetime import UTC, datetime

from sqlalchemy import select

from app.config import settings
from app.database import async_session
from app.email_service import send_store_credentials_email
from app.helm_client import helm_client
from app.k8s_client import k8s_client
from app.models import Store, StoreStatus, StoreType, User

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
    if store_type == StoreType.WOOCOMMERCE:
        return f"https://{store_name}.{settings.BASE_DOMAIN}/wp-admin"
    elif store_type == StoreType.MEDUSA:
        return f"https://{store_name}.{settings.BASE_DOMAIN}/admin"
    return f"https://{store_name}.{settings.BASE_DOMAIN}"


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

        # Step 4: Add /etc/hosts entry for local DNS (non-cluster mode)
        if not settings.IN_CLUSTER:
            self._add_hosts_entry(store.name)

        # Step 5: Update store record with URLs
        store_url = _get_store_url(store.name)
        admin_url = _get_admin_url(store.name, store.store_type)

        credentials_meta = {
            "admin_user": "admin",
            "admin_password": wp_password,
            "db_password": db_password,
            "helm_release": store.name,
        }

        await self._update_store_status(
            store.id,
            StoreStatus.READY,
            store_url=store_url,
            admin_url=admin_url,
            metadata_json=credentials_meta,
        )
        logger.info("[%s] Store provisioned successfully at %s", store.name, store_url)

        # Step 6: Email credentials to the store owner
        await self._send_credentials_email(
            store=store,
            store_url=store_url,
            admin_url=admin_url,
            admin_user="admin",
            admin_password=wp_password,
            db_password=db_password,
        )

    async def delete_store(self, store: Store) -> None:
        """Background task: tear down a store cleanly."""
        try:
            await self._update_store_status(store.id, StoreStatus.DELETING)

            # Step 1: Uninstall Helm release
            logger.info("[%s] Uninstalling Helm release", store.name)
            success, output = await helm_client.uninstall(store.name, store.namespace)
            if not success:
                logger.warning("[%s] Helm uninstall warning: %s", store.name, output)

            # Step 2: Delete namespace and WAIT for it to fully disappear
            # This is critical — K8s namespace deletion is async and can take time.
            # We must wait so the store name can be reused immediately.
            logger.info(
                "[%s] Deleting namespace %s (waiting for full cleanup)", store.name, store.namespace
            )
            k8s_client.delete_namespace(store.namespace, wait=True)

            # Step 2.5: Remove /etc/hosts entry (non-cluster mode)
            if not settings.IN_CLUSTER:
                self._remove_hosts_entry(store.name)

            # Step 3: Remove from DB — only AFTER namespace is fully gone
            async with async_session() as session:
                result = await session.execute(select(Store).where(Store.id == store.id))
                db_store = result.scalar_one_or_none()
                if db_store:
                    await session.delete(db_store)
                    await session.commit()

            logger.info("[%s] Store deleted successfully (namespace fully cleaned up)", store.name)

        except Exception as e:
            logger.exception("Failed to delete store %s: %s", store.name, e)
            await self._update_store_status(
                store.id, StoreStatus.FAILED, error=f"Delete failed: {e}"
            )

    def _get_chart_path(self, store_type: StoreType) -> str:
        """Resolve the Helm chart path for a store type."""
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "helm"))
        if store_type == StoreType.WOOCOMMERCE:
            return os.path.join(base, "woocommerce")
        elif store_type == StoreType.MEDUSA:
            return os.path.join(base, "medusa")
        else:
            raise ValueError(f"Unsupported store type: {store_type}")

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

    def _add_hosts_entry(self, store_name: str):
        """Add /etc/hosts entry for local DNS resolution using helper script."""
        hostname = f"{store_name}.{settings.BASE_DOMAIN}"
        script_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "update-hosts.sh")
        )

        # Check if entry already exists
        try:
            with open("/etc/hosts") as f:
                if hostname in f.read():
                    logger.info("[%s] /etc/hosts entry already exists", store_name)
                    return
        except Exception:
            pass

        # Try using the helper script with sudo (sudoers rule allows NOPASSWD)
        if os.path.exists(script_path):
            try:
                result = subprocess.run(
                    ["sudo", "-n", script_path, "add", store_name, hostname],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    logger.info("[%s] Added /etc/hosts entry: %s", store_name, hostname)
                    return
                else:
                    logger.warning("[%s] Script failed: %s", store_name, result.stderr)
            except Exception as e:
                logger.warning("[%s] Script error: %s", store_name, e)

        # Fallback: direct sudo tee
        entry = f"127.0.0.1 {hostname}"
        try:
            result = subprocess.run(
                ["sudo", "-n", "tee", "-a", "/etc/hosts"],
                input=f"\n{entry}\n",
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                logger.info("[%s] Added /etc/hosts entry via tee: %s", store_name, entry)
            else:
                logger.warning(
                    "[%s] Cannot write /etc/hosts. Install sudoers rule: "
                    "sudo cp scripts/urumi-ai-sudoers /etc/sudoers.d/urumi-ai",
                    store_name,
                )
        except Exception as e:
            logger.warning("[%s] Failed to update /etc/hosts: %s", store_name, e)

    def _remove_hosts_entry(self, store_name: str):
        """Remove /etc/hosts entry on store deletion using helper script."""
        hostname = f"{store_name}.{settings.BASE_DOMAIN}"
        script_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "update-hosts.sh")
        )

        # Try using the helper script with sudo (sudoers rule allows NOPASSWD)
        if os.path.exists(script_path):
            try:
                result = subprocess.run(
                    ["sudo", "-n", script_path, "remove", store_name],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    logger.info("[%s] Removed /etc/hosts entry for %s", store_name, hostname)
                    return
                else:
                    logger.warning("[%s] Script failed: %s", store_name, result.stderr)
            except Exception as e:
                logger.warning("[%s] Script error: %s", store_name, e)

        # Fallback: use sudo sed
        try:
            result = subprocess.run(
                ["sudo", "-n", "sed", "-i", f"/{hostname}/d", "/etc/hosts"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                logger.info("[%s] Removed /etc/hosts entry for %s", store_name, hostname)
            else:
                logger.warning(
                    "[%s] Cannot write /etc/hosts. Install sudoers rule: "
                    "sudo cp scripts/urumi-ai-sudoers /etc/sudoers.d/urumi-ai",
                    store_name,
                )
        except Exception as e:
            logger.warning("[%s] Failed to clean /etc/hosts: %s", store_name, e)

    def _build_helm_values(self, store: Store, wp_password: str, db_password: str) -> dict:
        """Build Helm --set values for store provisioning."""
        base_values = {
            "storeName": store.name,
            "baseDomain": settings.BASE_DOMAIN,
            "ingress.className": settings.INGRESS_CLASS,
            "ingress.host": f"{store.name}.{settings.BASE_DOMAIN}",
        }

        if store.store_type == StoreType.WOOCOMMERCE:
            base_values.update(
                {
                    "wordpress.adminUser": "admin",
                    "wordpress.adminPassword": wp_password,
                    "wordpress.adminEmail": f"admin@{store.name}.{settings.BASE_DOMAIN}",
                    "mysql.rootPassword": db_password,
                    "mysql.database": "wordpress",
                    "mysql.user": "wordpress",
                    "mysql.password": db_password,
                }
            )
        elif store.store_type == StoreType.MEDUSA:
            jwt_secret = _generate_password(32)
            cookie_secret = _generate_password(32)
            base_values.update(
                {
                    "medusa.adminEmail": f"admin@{store.name}.{settings.BASE_DOMAIN}",
                    "medusa.adminPassword": wp_password,
                    "medusa.jwtSecret": jwt_secret,
                    "medusa.cookieSecret": cookie_secret,
                    "postgres.database": "medusa",
                    "postgres.user": "medusa",
                    "postgres.password": db_password,
                }
            )

        return base_values

    async def _send_credentials_email(
        self,
        store: Store,
        store_url: str,
        admin_url: str,
        admin_user: str,
        admin_password: str,
        db_password: str,
    ) -> None:
        """Look up the store owner's email and send them the credentials."""
        try:
            async with async_session() as session:
                result = await session.execute(select(User).where(User.id == store.user_id))
                user = result.scalar_one_or_none()

            if not user:
                logger.warning(
                    "[%s] Cannot send email — user_id %s not found",
                    store.name,
                    store.user_id,
                )
                return

            # Build extra fields for Medusa stores
            extra: dict | None = None
            if store.store_type == StoreType.MEDUSA:
                extra = {
                    "admin_email": f"admin@{store.name}.{settings.BASE_DOMAIN}",
                }

            sent = send_store_credentials_email(
                recipient_email=user.email,
                store_name=store.name,
                store_type=store.store_type.value.title(),
                store_url=store_url,
                admin_url=admin_url,
                admin_user=admin_user,
                admin_password=admin_password,
                db_password=db_password,
                extra=extra,
            )

            if sent:
                logger.info("[%s] Credential email sent to %s", store.name, user.email)
            else:
                logger.warning(
                    "[%s] Credential email NOT sent (SMTP not configured or error). "
                    "Credentials are still saved in the database metadata.",
                    store.name,
                )
        except Exception as e:
            # Email failure should never block provisioning
            logger.exception("[%s] Failed to send credential email: %s", store.name, e)

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
