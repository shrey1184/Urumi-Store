# MedusaJS Helm Chart

Production-ready MedusaJS e-commerce platform deployment for Kubernetes.

## Quick Start

```bash
# Generate secrets
JWT_SECRET=$(openssl rand -base64 32)
COOKIE_SECRET=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 16)
ADMIN_PASSWORD=$(openssl rand -base64 12)

# Install
helm install my-store . \
  --set storeName="my-store" \
  --set baseDomain="local.store.dev" \
  --set medusa.adminPassword="${ADMIN_PASSWORD}" \
  --set medusa.jwtSecret="${JWT_SECRET}" \
  --set medusa.cookieSecret="${COOKIE_SECRET}" \
  --set postgres.password="${POSTGRES_PASSWORD}"
```

## What's Included

- **MedusaJS Backend** (Port 9000)
  - REST & GraphQL APIs
  - Admin Dashboard
  - Product/Order/Customer management
  
- **Next.js Storefront** (Port 8000)
  - Modern e-commerce UI
  - Shopping cart & checkout
  - Customer accounts
  
- **PostgreSQL 15** (Port 5432)
  - Persistent storage
  - Auto-migrations
  
- **Redis 7** (Port 6379)
  - Session management
  - Cart persistence

## Values

### Required Parameters
```yaml
storeName: "my-store"                    # Store identifier
baseDomain: "local.store.dev"            # Base domain
medusa.adminPassword: "changeme"         # Admin password
medusa.jwtSecret: "random-secret"        # JWT signing key
medusa.cookieSecret: "random-secret"     # Cookie encryption
postgres.password: "changeme"            # Database password
```

### Optional Parameters
```yaml
medusa:
  replicas: 1                            # Number of backend pods
  seedDemoData: false                    # Load demo products
  adminEmail: "admin@store.local"        # Admin email
  resources:
    limits:
      cpu: "2"
      memory: 2Gi

storefront:
  enabled: true                          # Enable storefront
  replicas: 1                            # Number of storefront pods
  resources:
    limits:
      cpu: "1"
      memory: 1Gi

postgres:
  storage:
    size: 5Gi                            # Database storage
    storageClass: ""                     # Storage class (default)

redis:
  enabled: true                          # Enable Redis cache
```

## Examples

### Local Development (Kind)
```bash
helm install dev-store . \
  --values values-local.yaml \
  --set medusa.adminPassword="dev123" \
  --set medusa.jwtSecret="dev-jwt-secret" \
  --set medusa.cookieSecret="dev-cookie-secret" \
  --set postgres.password="devpg123"
```

### Production (Cloud)
```bash
helm install prod-store . \
  --values values-prod.yaml \
  --set baseDomain="mystore.com" \
  --set medusa.adminPassword="${ADMIN_PASSWORD}" \
  --set medusa.jwtSecret="${JWT_SECRET}" \
  --set medusa.cookieSecret="${COOKIE_SECRET}" \
  --set postgres.password="${POSTGRES_PASSWORD}"
```

## Access

After deployment:
- **Storefront**: `http://{storeName}.{baseDomain}/`
- **Admin Panel**: `http://{storeName}.{baseDomain}/admin`
- **API**: `http://{storeName}.{baseDomain}/store`

## Upgrade

```bash
helm upgrade my-store . \
  --reuse-values \
  --set medusa.replicas=3
```

## Uninstall

```bash
helm uninstall my-store

# Optional: Delete persistent data
kubectl delete pvc -l app.kubernetes.io/name=medusa
```

## Requirements

- Kubernetes 1.20+
- Helm 3.8+
- Ingress controller (nginx/traefik)
- 4GB+ RAM available
- 10GB+ storage

## Chart Structure

```
medusa/
├── Chart.yaml              # Chart metadata
├── values.yaml             # Default values
├── values-local.yaml       # Local development overrides
├── values-prod.yaml        # Production overrides
└── templates/
    ├── _helpers.tpl        # Template helpers
    ├── medusa-deployment.yaml      # Backend deployment
    ├── medusa-service.yaml         # Backend service
    ├── medusa-init-job.yaml        # Database init job
    ├── medusa-config.yaml          # Medusa configuration
    ├── storefront-deployment.yaml  # Storefront deployment
    ├── storefront-service.yaml     # Storefront service
    ├── postgres-statefulset.yaml   # Database
    ├── postgres-service.yaml       # Database service
    ├── redis-deployment.yaml       # Cache
    ├── redis-service.yaml          # Cache service
    ├── pvc.yaml                    # Storage claims
    ├── secrets.yaml                # Secrets
    └── ingress.yaml                # Ingress rules
```

## Troubleshooting

**Pods not starting:**
```bash
kubectl get pods -l app.kubernetes.io/name=medusa
kubectl describe pod {pod-name}
kubectl logs {pod-name}
```

**Database issues:**
```bash
kubectl exec -it {storeName}-postgres-0 -- psql -U medusa
```

**Reset deployment:**
```bash
helm uninstall my-store
kubectl delete pvc -l app.kubernetes.io/name=medusa
helm install my-store . --values values-local.yaml ...
```

## Documentation

See [MEDUSA_DEPLOYMENT.md](../../Docs/MEDUSA_DEPLOYMENT.md) for complete documentation.
