# MedusaJS Deployment Guide

## Overview
Production-ready MedusaJS e-commerce platform deployment with:
- **Backend**: Official MedusaJS v2.0+ with REST/GraphQL APIs
- **Storefront**: Next.js 14 with App Router
- **Database**: PostgreSQL 15 with migrations
- **Cache**: Redis 7 for session/cart management
- **Admin Panel**: Built-in Medusa Admin Dashboard

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Ingress                              │
│              (nginx/traefik + TLS/SSL)                       │
└───────────────┬─────────────────────┬───────────────────────┘
                │                     │
                │                     │
        ┌───────▼──────┐      ┌──────▼────────┐
        │  Storefront  │      │  Medusa API   │
        │  (Next.js)   │◄─────┤   (Node.js)   │
        │  Port: 8000  │      │  Port: 9000   │
        └──────────────┘      └───────┬───────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
            ┌───────▼────────┐  ┌────▼─────┐  ┌───────▼──────┐
            │   PostgreSQL   │  │  Redis   │  │  Admin Panel │
            │   Port: 5432   │  │ Port:6379│  │  Port: 7001  │
            └────────────────┘  └──────────┘  └──────────────┘
```

## Features Implemented

### ✅ Complete MedusaJS Installation
- Official Medusa starter template
- Full product/order/customer management
- Payment gateway support (Stripe ready)
- Multi-region & multi-currency support
- Inventory management
- Discount codes & promotions
- Tax calculations

### ✅ Next.js Storefront
- Server-side rendering (SSR)
- Product catalog with search
- Shopping cart with Redis persistence
- Checkout flow
- Customer accounts
- Order history
- Responsive design

### ✅ Admin Dashboard
- Product management
- Order processing
- Customer management
- Analytics & reporting
- Inventory tracking
- Promotion management

### ✅ Infrastructure
- Auto-scaling deployments
- Health checks & readiness probes
- Database migrations on startup
- Persistent storage for uploads
- Redis caching layer
- TLS/SSL support

## Deployment

### Prerequisites
```bash
# Generate secure secrets
JWT_SECRET=$(openssl rand -base64 32)
COOKIE_SECRET=$(openssl rand -base64 32)
POSTGRES_PASSWORD=$(openssl rand -base64 16)
ADMIN_PASSWORD=$(openssl rand -base64 12)
```

### Local Deployment (Kind/k3d)
```bash
helm install my-store ./helm/medusa \
  --values ./helm/medusa/values-local.yaml \
  --set medusa.adminPassword="${ADMIN_PASSWORD}" \
  --set medusa.jwtSecret="${JWT_SECRET}" \
  --set medusa.cookieSecret="${COOKIE_SECRET}" \
  --set postgres.password="${POSTGRES_PASSWORD}" \
  --set storeName="demo-store"
```

### Production Deployment (VPS/Cloud)
```bash
helm install production-store ./helm/medusa \
  --values ./helm/medusa/values-prod.yaml \
  --set medusa.adminPassword="${ADMIN_PASSWORD}" \
  --set medusa.jwtSecret="${JWT_SECRET}" \
  --set medusa.cookieSecret="${COOKIE_SECRET}" \
  --set postgres.password="${POSTGRES_PASSWORD}" \
  --set storeName="production-store" \
  --set baseDomain="yourdomain.com"
```

## Post-Deployment

### Access Points
- **Storefront**: `http://{storeName}.{baseDomain}/`
- **Admin Panel**: `http://{storeName}.{baseDomain}/admin`
- **API**: `http://{storeName}.{baseDomain}/store`
- **Health Check**: `http://{storeName}.{baseDomain}/health`

### Admin Login
```
Email: admin@{storeName}.{baseDomain}
Password: [set during deployment]
```

### Verify Installation
```bash
# Check all pods are running
kubectl get pods -l app.kubernetes.io/name=medusa

# Check migrations completed
kubectl logs -l app.kubernetes.io/component=init

# Test API
curl http://{storeName}.{baseDomain}/health

# Test storefront
curl http://{storeName}.{baseDomain}/

# Test admin API
curl http://{storeName}.{baseDomain}/admin/auth
```

## Configuration

### Environment Variables (secrets)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `JWT_SECRET`: JWT token signing secret
- `COOKIE_SECRET`: Session cookie secret
- `ADMIN_EMAIL`: Initial admin user email
- `ADMIN_PASSWORD`: Initial admin user password

### Customization Options (values.yaml)
```yaml
medusa:
  replicas: 1              # Scale horizontally
  seedDemoData: true       # Load demo products
  adminEmail: "admin@..."  # Admin user email
  
storefront:
  enabled: true            # Enable/disable storefront
  replicas: 1              # Scale horizontally
  
postgres:
  storage:
    size: 5Gi              # Database storage
    
redis:
  enabled: true            # Enable/disable Redis
```

## Database Migrations

Migrations run automatically on:
1. **Init Job**: First-time setup
2. **Deployment startup**: Each pod checks migrations

Manual migration:
```bash
kubectl exec -it deployment/{storeName}-medusa -- npx medusa migrations run
```

## Scaling

### Horizontal Scaling
```bash
# Scale backend
kubectl scale deployment/{storeName}-medusa --replicas=3

# Scale storefront
kubectl scale deployment/{storeName}-storefront --replicas=3
```

### Vertical Scaling
Update `values.yaml` resources and upgrade:
```bash
helm upgrade {storeName} ./helm/medusa \
  --reuse-values \
  --set medusa.resources.limits.memory=2Gi
```

## Monitoring

### Health Checks
- **Liveness**: Ensures pod is running
- **Readiness**: Ensures pod can serve traffic

### Logs
```bash
# Backend logs
kubectl logs -f deployment/{storeName}-medusa

# Storefront logs
kubectl logs -f deployment/{storeName}-storefront

# Init job logs
kubectl logs job/{storeName}-medusa-init
```

## Backup & Recovery

### Database Backup
```bash
# Create backup
kubectl exec -it statefulset/{storeName}-postgres -- \
  pg_dump -U medusa medusa > backup.sql

# Restore backup
kubectl exec -i statefulset/{storeName}-postgres -- \
  psql -U medusa medusa < backup.sql
```

### Data Persistence
- PostgreSQL: StatefulSet with PVC
- Medusa uploads: PVC mounted at `/app/medusa/uploads`
- Redis: In-memory (ephemeral)

## Troubleshooting

### Common Issues

**Pods not starting:**
```bash
kubectl describe pod/{storeName}-medusa-xxx
kubectl logs pod/{storeName}-medusa-xxx
```

**Database connection failed:**
```bash
# Check PostgreSQL is ready
kubectl exec -it statefulset/{storeName}-postgres -- \
  pg_isready -U medusa

# Verify connection string
kubectl get secret/{storeName}-medusa-secret -o yaml
```

**Migrations failed:**
```bash
# Check init job
kubectl logs job/{storeName}-medusa-init

# Re-run init job
kubectl delete job/{storeName}-medusa-init
helm upgrade {storeName} ./helm/medusa --reuse-values
```

**Storefront can't connect to backend:**
```bash
# Verify Medusa service
kubectl get svc {storeName}-medusa

# Check connectivity
kubectl run -it --rm debug --image=busybox -- \
  wget -O- http://{storeName}-medusa:9000/health
```

## Security Best Practices

1. **Secrets Management**
   - Never commit secrets to Git
   - Use strong random passwords
   - Rotate secrets regularly

2. **Network Policies**
   - Restrict pod-to-pod communication
   - Use TLS for external traffic

3. **Access Control**
   - Enable RBAC
   - Limit admin access
   - Use strong admin passwords

4. **Database Security**
   - Use SSL for database connections
   - Regular backups
   - Limit database user permissions

## API Examples

### Get Products
```bash
curl http://{storeName}.{baseDomain}/store/products
```

### Create Order
```bash
curl -X POST http://{storeName}.{baseDomain}/store/carts \
  -H "Content-Type: application/json" \
  -d '{"items": [{"variant_id": "...", "quantity": 1}]}'
```

### Admin Authentication
```bash
curl -X POST http://{storeName}.{baseDomain}/admin/auth \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@...","password": "..."}'
```

## Integration

### Payment Providers
Configure in `medusa-config.js`:
- Stripe
- PayPal
- Manual payment

### Fulfillment Providers
- Manual fulfillment
- Custom shipping providers
- Third-party integrations

### Notification Providers
- SendGrid (email)
- Twilio (SMS)
- Custom webhooks

## Upgrading

```bash
# Backup first!
kubectl exec -it statefulset/{storeName}-postgres -- \
  pg_dump -U medusa medusa > backup-$(date +%Y%m%d).sql

# Upgrade Helm chart
helm upgrade {storeName} ./helm/medusa \
  --values ./helm/medusa/values.yaml \
  --reuse-values

# Monitor rollout
kubectl rollout status deployment/{storeName}-medusa
```

## Development

### Local Development Setup
```bash
# Port forward Medusa backend
kubectl port-forward svc/{storeName}-medusa 9000:9000

# Port forward storefront
kubectl port-forward svc/{storeName}-storefront 8000:8000

# Access admin locally
open http://localhost:9000/admin
```

### Custom Plugins
Mount custom plugins via ConfigMap or build custom Docker image.

## Support

- **Medusa Docs**: https://docs.medusajs.com
- **Medusa Discord**: https://discord.gg/medusajs
- **GitHub Issues**: https://github.com/medusajs/medusa

## Next Steps

1. Configure payment gateway (Stripe recommended)
2. Set up email provider (SendGrid/Mailgun)
3. Configure shipping rates
4. Add custom products
5. Customize storefront theme
6. Set up analytics (Google Analytics/Plausible)
7. Configure CDN for static assets
8. Set up monitoring (Prometheus/Grafana)

---

**Version**: 1.0.0  
**MedusaJS**: v2.0+  
**Last Updated**: February 2026
