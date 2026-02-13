"""
Kubernetes client wrapper — handles both in-cluster and kubeconfig auth.
"""

import logging

from kubernetes import client
from kubernetes import config as k8s_config
from kubernetes.client.rest import ApiException

from app.config import settings

logger = logging.getLogger(__name__)


class KubernetesClient:
    """Singleton-style K8s client wrapper."""

    def __init__(self):
        self._core_v1: client.CoreV1Api | None = None
        self._apps_v1: client.AppsV1Api | None = None
        self._networking_v1: client.NetworkingV1Api | None = None
        self._connected = False

    def connect(self):
        """Load kubeconfig or in-cluster config."""
        try:
            if settings.IN_CLUSTER:
                k8s_config.load_incluster_config()
                logger.info("Loaded in-cluster Kubernetes config")
            else:
                # Only pass config_file if explicitly set, otherwise use default
                if settings.KUBECONFIG:
                    k8s_config.load_kube_config(config_file=settings.KUBECONFIG)
                    logger.info("Loaded kubeconfig from %s", settings.KUBECONFIG)
                else:
                    k8s_config.load_kube_config()
                    logger.info("Loaded kubeconfig from default location (~/.kube/config)")

            self._core_v1 = client.CoreV1Api()
            self._apps_v1 = client.AppsV1Api()
            self._networking_v1 = client.NetworkingV1Api()
            self._connected = True
            logger.info("✓ Successfully connected to Kubernetes")
        except Exception as e:
            logger.error("Failed to connect to Kubernetes: %s", e, exc_info=True)
            self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def core_v1(self) -> client.CoreV1Api:
        if not self._core_v1:
            self.connect()
        return self._core_v1

    @property
    def apps_v1(self) -> client.AppsV1Api:
        if not self._apps_v1:
            self.connect()
        return self._apps_v1

    @property
    def networking_v1(self) -> client.NetworkingV1Api:
        if not self._networking_v1:
            self.connect()
        return self._networking_v1

    def namespace_exists(self, namespace: str) -> bool:
        try:
            self.core_v1.read_namespace(name=namespace)
            return True
        except ApiException as e:
            if e.status == 404:
                return False
            raise

    def get_namespace_status(self, namespace: str) -> str | None:
        """Get namespace phase: 'Active', 'Terminating', or None if not found."""
        try:
            ns = self.core_v1.read_namespace(name=namespace)
            return ns.status.phase
        except ApiException as e:
            if e.status == 404:
                return None
            raise

    def wait_for_namespace_deletion(
        self, namespace: str, timeout: int = 120, poll_interval: int = 3
    ) -> bool:
        """Block until a namespace is fully deleted. Returns True if gone, False on timeout.

        NOTE: This uses synchronous sleep. When called from async code, wrap with
        asyncio.to_thread() to avoid blocking the event loop.
        """
        import time

        deadline = time.time() + timeout
        while time.time() < deadline:
            status = self.get_namespace_status(namespace)
            if status is None:
                logger.info("Namespace %s fully deleted", namespace)
                return True
            logger.info(
                "Waiting for namespace %s to be deleted (status=%s)...",
                namespace,
                status,
            )
            time.sleep(poll_interval)
        logger.error(
            "Timed out waiting for namespace %s to be deleted after %ds",
            namespace,
            timeout,
        )
        return False

    def force_delete_namespace(self, namespace: str):
        """Force-remove finalizers from a stuck-terminating namespace."""
        try:
            ns = self.core_v1.read_namespace(name=namespace)
            if ns.spec.finalizers:
                ns.spec.finalizers = []
                self.core_v1.replace_namespace_finalize(name=namespace, body=ns)
                logger.info("Removed finalizers from namespace %s", namespace)
        except ApiException as e:
            if e.status == 404:
                logger.info("Namespace %s already gone", namespace)
            else:
                logger.warning("Failed to force-delete namespace %s: %s", namespace, e)

    def create_namespace(self, namespace: str, labels: dict | None = None):
        """Create a namespace with labels. Waits if namespace is terminating."""
        # If namespace is currently terminating, wait for it to fully disappear
        ns_status = self.get_namespace_status(namespace)
        if ns_status == "Terminating":
            logger.info("Namespace %s is still terminating, waiting for cleanup...", namespace)
            deleted = self.wait_for_namespace_deletion(namespace, timeout=120)
            if not deleted:
                # Try to force-remove finalizers and wait a bit more
                logger.warning(
                    "Namespace %s stuck terminating, attempting force cleanup", namespace
                )
                self.force_delete_namespace(namespace)
                deleted = self.wait_for_namespace_deletion(namespace, timeout=30)
                if not deleted:
                    raise RuntimeError(
                        f"Namespace {namespace} is stuck in Terminating state. "
                        f"Please wait a moment and try again, or manually clean it up "
                        f"with: kubectl delete ns {namespace} --force --grace-period=0"
                    )

        body = client.V1Namespace(
            metadata=client.V1ObjectMeta(
                name=namespace,
                labels=labels or {"managed-by": "store-platform", "type": "store"},
            )
        )
        try:
            self.core_v1.create_namespace(body=body)
            logger.info("Created namespace %s", namespace)
        except ApiException as e:
            if e.status == 409:
                logger.warning("Namespace %s already exists (idempotent)", namespace)
            elif e.status == 403 and "being terminated" in str(e.body):
                raise RuntimeError(
                    f"Namespace {namespace} is being terminated by Kubernetes. "
                    f"Please wait a moment and try creating the store again."
                )
            else:
                raise

    def delete_namespace(self, namespace: str, wait: bool = True):
        """Delete a namespace and all resources within it."""
        try:
            self.core_v1.delete_namespace(
                name=namespace,
                body=client.V1DeleteOptions(
                    propagation_policy="Background", grace_period_seconds=0
                ),
            )
            logger.info("Initiated deletion of namespace %s", namespace)
        except ApiException as e:
            if e.status == 404:
                logger.warning("Namespace %s not found during deletion", namespace)
                return
            else:
                raise

        # Wait for namespace to be fully gone so the name can be reused immediately
        if wait:
            deleted = self.wait_for_namespace_deletion(namespace, timeout=120)
            if not deleted:
                logger.warning(
                    "Namespace %s stuck terminating, attempting force cleanup", namespace
                )
                self.force_delete_namespace(namespace)
                self.wait_for_namespace_deletion(namespace, timeout=30)

    def get_namespace_pods(self, namespace: str) -> list:
        """Get all pods in a namespace."""
        try:
            pods = self.core_v1.list_namespaced_pod(namespace=namespace)
            return [
                {
                    "name": pod.metadata.name,
                    "status": pod.status.phase,
                    "ready": all(c.ready for c in (pod.status.container_statuses or [])),
                }
                for pod in pods.items
            ]
        except ApiException as e:
            if e.status == 404:
                return []
            raise

    def apply_resource_quota(self, namespace: str):
        """Apply ResourceQuota for multi-tenant isolation."""
        quota = client.V1ResourceQuota(
            metadata=client.V1ObjectMeta(name="store-quota"),
            spec=client.V1ResourceQuotaSpec(
                hard={
                    "pods": "20",
                    "requests.cpu": "2",
                    "requests.memory": "4Gi",
                    "limits.cpu": "4",
                    "limits.memory": "8Gi",
                    "persistentvolumeclaims": "5",
                    "requests.storage": "20Gi",
                }
            ),
        )
        try:
            self.core_v1.create_namespaced_resource_quota(namespace=namespace, body=quota)
            logger.info("Applied ResourceQuota to %s", namespace)
        except ApiException as e:
            if e.status == 409:
                logger.warning("ResourceQuota already exists in %s", namespace)
            else:
                raise

    def apply_limit_range(self, namespace: str):
        """Apply LimitRange for default container limits."""
        limit_range = client.V1LimitRange(
            metadata=client.V1ObjectMeta(name="store-limits"),
            spec=client.V1LimitRangeSpec(
                limits=[
                    client.V1LimitRangeItem(
                        type="Container",
                        default={"cpu": "500m", "memory": "512Mi"},
                        default_request={"cpu": "100m", "memory": "128Mi"},
                        max={"cpu": "2", "memory": "4Gi"},
                    )
                ]
            ),
        )
        try:
            self.core_v1.create_namespaced_limit_range(namespace=namespace, body=limit_range)
            logger.info("Applied LimitRange to %s", namespace)
        except ApiException as e:
            if e.status == 409:
                logger.warning("LimitRange already exists in %s", namespace)
            else:
                raise

    def create_tls_secret(
        self, namespace: str, secret_name: str, cert_data: bytes, key_data: bytes
    ):
        """Create a TLS secret in the namespace."""
        secret = client.V1Secret(
            metadata=client.V1ObjectMeta(name=secret_name),
            type="kubernetes.io/tls",
            data={
                "tls.crt": cert_data,
                "tls.key": key_data,
            },
        )
        try:
            self.core_v1.create_namespaced_secret(namespace=namespace, body=secret)
            logger.info("Created TLS secret %s in %s", secret_name, namespace)
        except ApiException as e:
            if e.status == 409:
                logger.warning("TLS secret %s already exists in %s", secret_name, namespace)
            else:
                raise


# Global singleton
k8s_client = KubernetesClient()
