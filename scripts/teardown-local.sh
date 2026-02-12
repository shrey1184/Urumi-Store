#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────
#  Teardown script — destroys the local Kind cluster
# ──────────────────────────────────────────────────────────────
set -euo pipefail

CLUSTER_NAME="${CLUSTER_NAME:-store-platform}"

echo "→ Deleting Kind cluster '${CLUSTER_NAME}'..."
kind delete cluster --name "${CLUSTER_NAME}"
echo "✓ Cluster deleted"
