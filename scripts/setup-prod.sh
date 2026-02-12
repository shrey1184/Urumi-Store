#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
#  VPS / Production setup guide script (k3s)
# ──────────────────────────────────────────────────────────────
set -euo pipefail

echo "╔══════════════════════════════════════════════╗"
echo "║  Store Platform — VPS Production Setup (k3s) ║"
echo "╚══════════════════════════════════════════════╝"

# ── 1. Check prerequisites ──
for cmd in kubectl helm; do
  if ! command -v "$cmd" &> /dev/null; then
    echo "ERROR: '$cmd' is required."
    exit 1
  fi
done

# ── 2. Install k3s (if not present) ──
if ! command -v k3s &> /dev/null; then
  echo "→ Installing k3s..."
  curl -sfL https://get.k3s.io | sh -
  echo "→ Waiting for k3s to be ready..."
  sleep 10
  sudo chmod 644 /etc/rancher/k3s/k3s.yaml
  export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
  echo "✓ k3s installed"
else
  export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
  echo "✓ k3s already installed"
fi

# ── 3. Verify cluster ──
kubectl get nodes
echo "✓ Cluster is ready"

# ── 4. Create platform namespace ──
kubectl create namespace store-platform --dry-run=client -o yaml | kubectl apply -f -

echo ""
echo "══════════════════════════════════════════════════"
echo "  Production Setup Notes"
echo "══════════════════════════════════════════════════"
echo ""
echo "  1. Point your domain DNS to this VPS IP"
echo "  2. Set BASE_DOMAIN to your domain in .env"
echo "  3. Update helm/woocommerce/values-prod.yaml"
echo "  4. Install cert-manager for TLS (optional):"
echo "     kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.4/cert-manager.yaml"
echo ""
echo "  5. Start the backend:"
echo "     cd Backend && pip install -r requirements.txt"
echo "     KUBECONFIG=/etc/rancher/k3s/k3s.yaml uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "  6. Build & serve frontend:"
echo "     cd Frontend && npm run build"
echo "     # Serve dist/ via nginx or any static file server"
echo ""
echo "══════════════════════════════════════════════════"
