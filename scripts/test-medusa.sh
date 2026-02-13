#!/bin/bash
# Test MedusaJS deployment in Kind cluster

set -e

echo "=== MedusaJS Deployment Test ==="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
STORE_NAME="medusa-test"
NAMESPACE="default"

# Generate secrets
echo "📝 Generating secrets..."
JWT_SECRET=$(openssl rand -base64 32)
COOKIE_SECRET=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 16)
ADMIN_PASSWORD="Admin123!"

echo "  ✓ Secrets generated"
echo ""

# Check if Helm chart exists
if [ ! -f "./helm/medusa/Chart.yaml" ]; then
  echo -e "${RED}❌ MedusaJS Helm chart not found${NC}"
  echo "Run this script from the project root: ./scripts/test-medusa.sh"
  exit 1
fi

# Install/Upgrade Helm chart
echo "🚀 Deploying MedusaJS..."
helm upgrade --install ${STORE_NAME} ./helm/medusa \
  --values ./helm/medusa/values-local.yaml \
  --set storeName="${STORE_NAME}" \
  --set baseDomain="local.store.dev" \
  --set medusa.adminPassword="${ADMIN_PASSWORD}" \
  --set medusa.jwtSecret="${JWT_SECRET}" \
  --set medusa.cookieSecret="${COOKIE_SECRET}" \
  --set postgres.password="${POSTGRES_PASSWORD}" \
  --set medusa.seedDemoData=true \
  --namespace ${NAMESPACE}

echo ""
echo "⏳ Waiting for deployment..."
sleep 5

# Wait for init job
echo "  📦 Waiting for init job to complete..."
kubectl wait --for=condition=complete --timeout=600s job/${STORE_NAME}-medusa-init -n ${NAMESPACE} 2>/dev/null || {
  echo -e "${YELLOW}  ⚠ Init job still running, checking logs...${NC}"
  kubectl logs -f job/${STORE_NAME}-medusa-init -n ${NAMESPACE} --tail=20 || true
}

# Wait for pods
echo "  📦 Waiting for pods to be ready..."
kubectl wait --for=condition=ready --timeout=300s \
  pod -l app.kubernetes.io/name=medusa -n ${NAMESPACE} 2>/dev/null || {
  echo -e "${YELLOW}  ⚠ Some pods not ready yet${NC}"
}

echo ""
echo "📊 Deployment Status:"
kubectl get pods -l app.kubernetes.io/name=medusa -n ${NAMESPACE}

echo ""
echo "🔍 Checking services..."
kubectl get svc -l app.kubernetes.io/name=medusa -n ${NAMESPACE}

echo ""
echo "🌐 Checking ingress..."
kubectl get ingress -l app.kubernetes.io/name=medusa -n ${NAMESPACE}

echo ""
echo "=== 🎉 Deployment Complete ==="
echo ""
echo -e "${GREEN}Access URLs:${NC}"
echo "  Storefront:  http://${STORE_NAME}.local.store.dev"
echo "  Admin Panel: http://${STORE_NAME}.local.store.dev/admin"
echo "  API:         http://${STORE_NAME}.local.store.dev/store"
echo ""
echo -e "${GREEN}Admin Credentials:${NC}"
echo "  Email:    admin@${STORE_NAME}.local.store.dev"
echo "  Password: ${ADMIN_PASSWORD}"
echo ""

# Test endpoints
echo "🧪 Testing endpoints..."
sleep 10

# Health check
echo -n "  Health check: "
if curl -sf http://${STORE_NAME}.local.store.dev/health > /dev/null 2>&1; then
  echo -e "${GREEN}✓${NC}"
else
  echo -e "${RED}✗ (may need port-forward)${NC}"
  echo ""
  echo "Run: kubectl port-forward svc/${STORE_NAME}-medusa 9000:9000"
  echo "Then: curl http://localhost:9000/health"
fi

echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo "  1. Wait a few minutes for Medusa to fully initialize"
echo "  2. Access the admin panel and log in"
echo "  3. Create your first product"
echo "  4. View the storefront"
echo ""
echo "📚 Documentation: ./Docs/MEDUSA_DEPLOYMENT.md"
echo ""
echo "🐛 Troubleshooting:"
echo "  kubectl logs deployment/${STORE_NAME}-medusa"
echo "  kubectl logs job/${STORE_NAME}-medusa-init"
echo "  kubectl describe pod -l app.kubernetes.io/name=medusa"
echo ""
