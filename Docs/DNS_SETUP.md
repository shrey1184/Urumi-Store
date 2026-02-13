# DNS Resolution Setup for Local Development

## Problem
When creating new stores, the browser shows "This site can't be reached" with `ERR_NAME_NOT_RESOLVED` because local domains like `storename.local.store.dev` aren't resolvable.

## Solution
We've implemented automatic `/etc/hosts` management so new stores are immediately accessible in your browser.

## One-Time Setup

Run this once to configure your system:

```bash
cd /home/shrey/Urumi-Ai
./scripts/setup-hosts-manager.sh
```

This will:
- ✅ Configure passwordless sudo for hosts file updates
- ✅ Sync all existing store domains to `/etc/hosts`
- ✅ Enable automatic domain registration for new stores

## How It Works

### 1. Automatic (Recommended)
When you create a new store via the API, the backend automatically:
1. Creates Kubernetes resources
2. Adds the domain to `/etc/hosts`
3. Store is immediately accessible in browser

### 2. Manual Sync (If Needed)
If automatic updates don't work:

```bash
# Sync all stores from Kubernetes
./scripts/update-hosts.sh sync

# Add a specific store
./scripts/update-hosts.sh add storename storename.local.store.dev

# Remove a store
./scripts/update-hosts.sh remove storename

# Clean all Urumi-Ai entries
./scripts/update-hosts.sh clean
```

## Verification

Check if domains are registered:
```bash
cat /etc/hosts | grep local.store.dev
```

Test a store URL:
```bash
curl -I http://demo99.local.store.dev
```

## Troubleshooting

### Browser still can't reach the site

1. **Clear browser DNS cache**:
   - Chrome: Go to `chrome://net-internals/#dns` and click "Clear host cache"
   - Firefox: Close and restart the browser

2. **Verify /etc/hosts entry exists**:
   ```bash
   grep "yourstore.local.store.dev" /etc/hosts
   ```

3. **Manually sync**:
   ```bash
   ./scripts/update-hosts.sh sync
   ```

4. **Check ingress is ready**:
   ```bash
   kubectl get ingress -n store-yourstore
   ```

### Permission errors

If you see permission errors in backend logs:

```bash
# Re-run the setup script
./scripts/setup-hosts-manager.sh

# Or manually install sudoers rule
sudo cp scripts/urumi-ai-sudoers /etc/sudoers.d/urumi-ai
sudo chmod 0440 /etc/sudoers.d/urumi-ai
```

### Store shows as "ready" but site doesn't load

1. Check if pod is actually ready:
   ```bash
   kubectl get pods -n store-yourstore
   ```

2. Check ingress:
   ```bash
   kubectl get ingress -n store-yourstore
   ```

3. Check WordPress logs:
   ```bash
   kubectl logs -n store-yourstore deployment/yourstore-wordpress
   ```

## Files

- `scripts/update-hosts.sh` - Main hosts file manager
- `scripts/setup-hosts-manager.sh` - One-time setup script
- `scripts/urumi-ai-sudoers` - Sudoers configuration template
- `Backend/app/orchestrator.py` - Calls the update script automatically

## Production Notes

In production with real DNS:
- Set `IN_CLUSTER=true` in backend environment
- Configure proper DNS records pointing to your ingress controller
- Remove local `/etc/hosts` management
- Use cert-manager for TLS certificates
