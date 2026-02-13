#!/bin/bash
# Build MedusaJS Docker images and load them into the Kind cluster.
# Usage:  ./scripts/build-medusa-images.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$PROJECT_ROOT/helm/medusa/docker"
KIND_CLUSTER="${KIND_CLUSTER:-kind}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================="
echo "  MedusaJS Docker Image Builder"
echo "========================================="
echo ""

# ── 1. Build medusa-backend ──────────────────────────────────
echo -e "${YELLOW}[1/4]${NC} Building medusa-backend image..."
docker build \
  -t medusa-backend:latest \
  -f "$DOCKER_DIR/medusa-backend/Dockerfile" \
  "$DOCKER_DIR/medusa-backend"
echo -e "${GREEN}  ✓ medusa-backend:latest built${NC}"
echo ""

# ── 2. Build medusa-storefront ───────────────────────────────
echo -e "${YELLOW}[2/4]${NC} Building medusa-storefront image..."
docker build \
  -t medusa-storefront:latest \
  -f "$DOCKER_DIR/medusa-storefront/Dockerfile" \
  "$DOCKER_DIR/medusa-storefront"
echo -e "${GREEN}  ✓ medusa-storefront:latest built${NC}"
echo ""

# ── 3. Load into Kind ────────────────────────────────────────
echo -e "${YELLOW}[3/4]${NC} Loading images into Kind cluster '${KIND_CLUSTER}'..."
kind load docker-image medusa-backend:latest    --name "$KIND_CLUSTER"
kind load docker-image medusa-storefront:latest --name "$KIND_CLUSTER"
echo -e "${GREEN}  ✓ Images loaded into Kind${NC}"
echo ""

# ── 4. Verify ────────────────────────────────────────────────
echo -e "${YELLOW}[4/4]${NC} Verifying images..."
docker images | grep -E "medusa-backend|medusa-storefront" || true
echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  All MedusaJS images ready!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Next: Deploy with Helm"
echo "  helm upgrade --install <name> ./helm/medusa \\"
echo "    --values ./helm/medusa/values-local.yaml \\"
echo "    --set storeName=<name> \\"
echo "    --set medusa.adminPassword=<password> \\"
echo "    --set medusa.jwtSecret=\$(openssl rand -base64 32) \\"
echo "    --set medusa.cookieSecret=\$(openssl rand -base64 32) \\"
echo "    --set postgres.password=\$(openssl rand -base64 16) \\"
echo "    --namespace store-<name> --create-namespace"
echo ""
