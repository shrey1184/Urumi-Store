#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
#  Setup script for local Kubernetes cluster using Kind
#  Creates a cluster with ingress-ready node, installs nginx
#  ingress controller, and configures /etc/hosts for store URLs.
# ──────────────────────────────────────────────────────────────
set -euo pipefail

CLUSTER_NAME="${CLUSTER_NAME:-store-platform}"
BASE_DOMAIN="${BASE_DOMAIN:-local.store.dev}"

echo "╔══════════════════════════════════════════════╗"
echo "║  Store Provisioning Platform — Local Setup   ║"
echo "╚══════════════════════════════════════════════╝"

# ── 1. Check prerequisites ──
for cmd in kind kubectl helm docker; do
  if ! command -v "$cmd" &> /dev/null; then
    echo "ERROR: '$cmd' is required but not installed."
    echo "  kind:    https://kind.sigs.k8s.io/docs/user/quick-start/#installation"
    echo "  kubectl: https://kubernetes.io/docs/tasks/tools/"
    echo "  helm:    https://helm.sh/docs/intro/install/"
    echo "  docker:  https://docs.docker.com/get-docker/"
    exit 1
  fi
done
echo "✓ All prerequisites found"

# ── 2. Create Kind cluster ──
if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
  echo "✓ Kind cluster '${CLUSTER_NAME}' already exists"
else
  echo "→ Creating Kind cluster '${CLUSTER_NAME}'..."
  cat <<EOF | kind create cluster --name "${CLUSTER_NAME}" --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "ingress-ready=true"
    extraPortMappings:
      - containerPort: 80
        hostPort: 80
        protocol: TCP
      - containerPort: 443
        hostPort: 443
        protocol: TCP
EOF
  echo "✓ Kind cluster created"
fi

# ── 3. Install NGINX Ingress Controller ──
echo "→ Installing NGINX Ingress Controller..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

echo "→ Waiting for ingress controller to be ready..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s
echo "✓ NGINX Ingress Controller ready"

# ── 4. Create platform namespace ──
kubectl create namespace store-platform --dry-run=client -o yaml | kubectl apply -f -
echo "✓ Platform namespace ready"

# ── 5. Hosts file guidance ──
echo ""
echo "══════════════════════════════════════════════════"
echo "  IMPORTANT: Add store domains to /etc/hosts"
echo "══════════════════════════════════════════════════"
echo ""
echo "  When you create a store named 'my-store', add:"
echo ""
echo "    127.0.0.1  my-store.${BASE_DOMAIN}"
echo ""
echo "  Or use a wildcard DNS tool like dnsmasq:"
echo "    address=/.${BASE_DOMAIN}/127.0.0.1"
echo ""
echo "  Alternatively, you can use nip.io:"
echo "    Set BASE_DOMAIN=127.0.0.1.nip.io"
echo ""
echo "══════════════════════════════════════════════════"
echo ""
echo "✓ Local cluster setup complete!"
echo ""
echo "  Next steps:"
echo "  1. Start the backend:  cd Backend && pip install -r requirements.txt && uvicorn app.main:app --reload"
echo "  2. Start the frontend: cd Frontend && npm run dev"
echo "  3. Open http://localhost:5173 to access the dashboard"
