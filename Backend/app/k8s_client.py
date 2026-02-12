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

    def create_namespace(self, namespace: str, labels: dict | None = None):
        """Create a namespace with labels."""
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
            else:
                raise

    def delete_namespace(self, namespace: str):
        """Delete a namespace and all resources within it."""
        try:
            self.core_v1.delete_namespace(
                name=namespace,
                body=client.V1DeleteOptions(propagation_policy="Foreground"),
            )
            logger.info("Deleted namespace %s", namespace)
        except ApiException as e:
            if e.status == 404:
                logger.warning("Namespace %s not found during deletion", namespace)
            else:
                raise

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
