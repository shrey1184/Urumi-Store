#!/bin/bash
# Load required Docker images into kind cluster
# This is needed because kind cluster has DNS issues preventing direct pulls

set -e

IMAGES=(
    "mysql:8.0"
    "wordpress:6.4-apache"
    "wordpress:cli-2.9-php8.2"
    "busybox:1.36"
    "postgres:16-alpine"
    "redis:7-alpine"
)

echo "Loading images into kind cluster..."

for image in "${IMAGES[@]}"; do
    echo "→ Pulling $image..."
    docker pull "$image" || { echo "Failed to pull $image"; exit 1; }
    
    echo "→ Loading $image into kind..."
    docker save "$image" | docker exec -i kind-control-plane ctr -n k8s.io images import - || {
        echo "Failed to load $image into kind"
        exit 1
    }
done

echo "✓ All images loaded successfully!"
echo ""
echo "Available images in kind:"
docker exec kind-control-plane crictl images | grep -E "mysql|wordpress|busybox"
