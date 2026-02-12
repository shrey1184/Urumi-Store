# Fix for Store Access Issues

## Root Causes

1. **Kind cluster created without port mappings** - Your cluster doesn't have ports 80/443 forwarded
2. **No ingress controller** - The ingress resources exist but no controller processes them
3. **No DNS entries** - Domains not mapped (FIXED: added to /etc/hosts)

## Current Temporary Solution

**Your store is accessible NOW via NodePort:**
- Frontend: http://excellent-choice.local.store.dev:30081
- Admin: http://excellent-choice.local.store.dev:30081/wp-admin

## Permanent Fix: Recreate Kind Cluster

To use ingress properly (without port numbers), you MUST recreate your kind cluster:

```bash
# 1. Delete current cluster (WARNING: This removes all stores!)
kind delete cluster

# 2. Run the setup script which creates cluster correctly
cd /home/shrey/Urumi-Ai
./scripts/setup-local.sh

# 3. The script will:
#    - Create kind cluster with ports 80/443 mapped
#    - Install ingress controller
#    - Configure /etc/hosts
```

## After Recreating Cluster

You'll need to redeploy your stores:

```bash
# Redeploy excellent-choice store
helm install excellent-choice ./helm/woocommerce \
  --namespace store-excellent-choice \
  --create-namespace \
  --values ./helm/woocommerce/values-local.yaml \
  --set storeName=excellent-choice \
  --set wordpress.adminPassword="your-password" \
  --set mysql.rootPassword="your-root-password" \
  --set mysql.password="your-mysql-password"
```

## Why Your Current Cluster Doesn't Work

```bash
# Check current cluster ports (should show 80 and 443):
$ docker ps --filter name=kind-control-plane --format "{{.Ports}}"
127.0.0.1:43951->6443/tcp   # ❌ Only API server, no ingress ports!

# After recreating with setup-local.sh:
127.0.0.1:80->80/tcp, 127.0.0.1:443->443/tcp, ...  # ✅ Correct!
```

## Alternative: Continue Using NodePort

If you don't want to recreate the cluster, you can continue using NodePort:

1. For each store, expose the service:
```bash
kubectl patch svc <store-name>-wordpress -n store-<store-name> \
  -p '{"spec":{"type":"NodePort","ports":[{"port":80,"targetPort":80,"nodePort":30XXX}]}}'
```

2. Access via: `http://<store-name>.local.store.dev:30XXX`

**Note:** You'll need different NodePorts for each store (30081, 30082, etc.)
