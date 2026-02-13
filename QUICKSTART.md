# Quick Start Guide - DNS Resolution Fix

## ✅ Problem Solved!

Your stores are now automatically accessible in the browser after creation. No more "This site can't be reached" errors!

## What Was Fixed

1. **Timeout Issues**: 
   - Increased job timeout from 10 to 15 minutes
   - Fixed permission issues for WooCommerce installation
   - Set compatible WooCommerce version (8.9.3) for WordPress 6.4

2. **DNS Resolution**:
   - Created automatic `/etc/hosts` management script
   - Configured passwordless sudo for the hosts updater
   - Backend now calls the script to add domains automatically

## How to Use

### First Time Setup (Already Done!)

```bash
./scripts/setup-hosts-manager.sh
```

This configured your system for automatic DNS management.

### Creating New Stores

1. **Go to Dashboard**: http://localhost:5173
2. **Click "Create Store"**
3. **Enter store name** (e.g., "myshop")
4. **Select store type** (WooCommerce or MedusaJS)
5. **Click Create**

The store will be provisioning (takes 2-4 minutes). Once ready:
- ✅ Store URL will appear on the card
- ✅ Domain is automatically added to `/etc/hosts`
- ✅ Click the URL to access your store immediately!

### If DNS Doesn't Work Automatically

Sometimes the backend may not have permissions. Manually sync:

```bash
# Sync all stores at once
./scripts/update-hosts.sh sync

# Or add a specific store
./scripts/update-hosts.sh add storename storename.local.store.dev
```

### Verify Everything Works

```bash
# Check /etc/hosts entries
cat /etc/hosts | grep local.store.dev

# Test a store URL
curl -I http://yourstore.local.store.dev

# Check store status
curl http://localhost:8000/api/v1/stores
```

## Troubleshooting

### "This site can't be reached" Error

**Solution 1: Clear Browser DNS Cache**
- Chrome: `chrome://net-internals/#dns` → Clear host cache
- Firefox: Restart browser

**Solution 2: Manually Sync**
```bash
./scripts/update-hosts.sh sync
```

**Solution 3: Check if domain is in /etc/hosts**
```bash
grep "yourstore.local.store.dev" /etc/hosts
```

If not found, add it:
```bash
./scripts/update-hosts.sh add yourstore yourstore.local.store.dev
```

### Store Shows "Ready" But Site Doesn't Load

```bash
# Check pods are running
kubectl get pods -n store-yourstore

# Check ingress
kubectl get ingress -n store-yourstore

# Check WordPress logs
kubectl logs -n store-yourstore deployment/yourstore-wordpress
```

### Permission Denied When Running Scripts

```bash
# Re-run the setup
./scripts/setup-hosts-manager.sh
```

## Files Changed

- ✅ `helm/woocommerce/templates/wp-setup-job.yaml` - Increased timeout, fixed permissions, compatible WooCommerce version
- ✅ `helm/medusa/templates/medusa-init-job.yaml` - Increased timeout for consistency
- ✅ `Backend/app/orchestrator.py` - Calls update-hosts.sh script
- ✅ `scripts/update-hosts.sh` - Manages /etc/hosts entries
- ✅ `scripts/setup-hosts-manager.sh` - One-time setup for passwordless sudo
- ✅ `scripts/urumi-ai-sudoers` - Sudoers configuration
- ✅ `Docs/DNS_SETUP.md` - Complete documentation
- ✅ `README.md` - Updated with DNS setup instructions

## Current Store Status

Check your stores:
```bash
curl -s http://localhost:8000/api/v1/stores | python3 -m json.tool
```

Working stores:
- ✅ saanestore (http://saanestore.local.store.dev)
- ✅ medusa-test (https://medusa-test.local.store.dev)
- ✅ demo99 (https://demo99.local.store.dev)
- ✅ finalstore (https://finalstore.local.store.dev)
- ✅ autotest (https://autotest.local.store.dev)

**You're all set! Create new stores and they'll work immediately! 🎉**
