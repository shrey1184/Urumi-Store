#!/bin/bash
# Script to update /etc/hosts with store domains
# Usage: ./update-hosts.sh add <store-name> <domain>
#        ./update-hosts.sh remove <store-name> <domain>
#        ./update-hosts.sh sync (sync from all ingresses)

set -e

ACTION="${1:-sync}"
STORE_NAME="${2}"
DOMAIN="${3}"

# Marker for our managed entries
MARKER="# Urumi-Ai Store Platform"

case "$ACTION" in
  add)
    if [ -z "$STORE_NAME" ] || [ -z "$DOMAIN" ]; then
      echo "Usage: $0 add <store-name> <domain>"
      exit 1
    fi
    
    # Check if entry already exists
    if grep -q "$DOMAIN" /etc/hosts; then
      echo "Entry for $DOMAIN already exists in /etc/hosts"
      exit 0
    fi
    
    # Add entry
    echo "127.0.0.1 $DOMAIN $MARKER:$STORE_NAME" | sudo tee -a /etc/hosts > /dev/null
    echo "✓ Added $DOMAIN to /etc/hosts"
    ;;
    
  remove)
    if [ -z "$STORE_NAME" ]; then
      echo "Usage: $0 remove <store-name>"
      exit 1
    fi
    
    # Remove entries for this store
    sudo sed -i "/$MARKER:$STORE_NAME/d" /etc/hosts
    echo "✓ Removed entries for $STORE_NAME from /etc/hosts"
    ;;
    
  sync)
    echo "Syncing /etc/hosts with Kubernetes ingresses..."
    
    # Get all ingresses and extract hosts
    INGRESSES=$(kubectl get ingress -A -o json | \
      jq -r '.items[] | 
        select(.metadata.namespace | startswith("store-")) | 
        "\(.metadata.labels."app.kubernetes.io/instance") \(.spec.rules[0].host)"' 2>/dev/null)
    
    if [ -z "$INGRESSES" ]; then
      echo "No store ingresses found"
      exit 0
    fi
    
    # Process each ingress
    echo "$INGRESSES" | while read -r STORE_NAME HOST; do
      # Check if entry exists
      if ! grep -q "$HOST" /etc/hosts; then
        echo "127.0.0.1 $HOST $MARKER:$STORE_NAME" | sudo tee -a /etc/hosts > /dev/null
        echo "✓ Added $HOST"
      else
        echo "  $HOST already exists"
      fi
    done
    
    echo "✓ Sync complete"
    ;;
    
  clean)
    echo "Cleaning all Urumi-Ai entries from /etc/hosts..."
    sudo sed -i "/$MARKER/d" /etc/hosts
    echo "✓ Cleaned all entries"
    ;;
    
  *)
    echo "Usage: $0 {add|remove|sync|clean}"
    echo ""
    echo "Commands:"
    echo "  add <store-name> <domain>  - Add a single store domain"
    echo "  remove <store-name>        - Remove all entries for a store"
    echo "  sync                       - Sync all store domains from K8s"
    echo "  clean                      - Remove all Urumi-Ai entries"
    exit 1
    ;;
esac
