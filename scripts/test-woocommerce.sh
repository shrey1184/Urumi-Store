#!/bin/bash
set -e

# ─────────────────────────────────────────────────────────────────────
# Test script for WooCommerce deployment
# ─────────────────────────────────────────────────────────────────────

STORE_NAME="${1:-woo-test}"
NAMESPACE="store-${STORE_NAME}"
BASE_DOMAIN="${2:-local.store.dev}"
HOST="${STORE_NAME}.${BASE_DOMAIN}"

echo "════════════════════════════════════════════════════════════════"
echo "Testing WooCommerce Store: $STORE_NAME"
echo "════════════════════════════════════════════════════════════════"
echo ""

# ─── Test 1: Check if namespace exists ───
echo "✓ Checking namespace..."
if kubectl get namespace "$NAMESPACE" &>/dev/null; then
    echo "  → Namespace '$NAMESPACE' exists"
else
    echo "  ✗ Namespace '$NAMESPACE' not found!"
    exit 1
fi
echo ""

# ─── Test 2: Check MySQL StatefulSet ───
echo "✓ Checking MySQL..."
MYSQL_READY=$(kubectl get statefulset -n "$NAMESPACE" -l app.kubernetes.io/component=mysql -o jsonpath='{.items[0].status.readyReplicas}')
if [ "$MYSQL_READY" = "1" ]; then
    echo "  → MySQL is ready"
else
    echo "  ✗ MySQL not ready (ready: $MYSQL_READY)"
    exit 1
fi
echo ""

# ─── Test 3: Check WordPress Deployment ───
echo "✓ Checking WordPress..."
WP_READY=$(kubectl get deployment -n "$NAMESPACE" -l app.kubernetes.io/component=wordpress -o jsonpath='{.items[0].status.readyReplicas}')
if [ "$WP_READY" -ge "1" ]; then
    echo "  → WordPress is ready ($WP_READY replicas)"
else
    echo "  ✗ WordPress not ready (ready: $WP_READY)"
    exit 1
fi
echo ""

# ─── Test 4: Check setup job ───
echo "✓ Checking setup job..."
JOB_STATUS=$(kubectl get jobs -n "$NAMESPACE" -l app.kubernetes.io/component=wp-setup -o jsonpath='{.items[0].status.succeeded}' 2>/dev/null || echo "0")
if [ "$JOB_STATUS" = "1" ]; then
    echo "  → Setup job completed successfully"
else
    echo "  ⚠ Setup job not completed yet"
    echo "  → Checking job logs..."
    kubectl logs -n "$NAMESPACE" -l app.kubernetes.io/component=wp-setup --tail=20 || true
fi
echo ""

# ─── Test 5: Check Services ───
echo "✓ Checking services..."
MYSQL_SVC=$(kubectl get svc -n "$NAMESPACE" "${STORE_NAME}-mysql" -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "")
WP_SVC=$(kubectl get svc -n "$NAMESPACE" "${STORE_NAME}-wordpress" -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "")

if [ -n "$MYSQL_SVC" ]; then
    echo "  → MySQL service: $MYSQL_SVC:3306"
else
    echo "  ✗ MySQL service not found!"
fi

if [ -n "$WP_SVC" ]; then
    echo "  → WordPress service: $WP_SVC:80"
else
    echo "  ✗ WordPress service not found!"
fi
echo ""

# ─── Test 6: Check Ingress ───
echo "✓ Checking ingress..."
INGRESS=$(kubectl get ingress -n "$NAMESPACE" -o jsonpath='{.items[0].spec.rules[0].host}' 2>/dev/null || echo "")
if [ -n "$INGRESS" ]; then
    echo "  → Ingress configured for: $INGRESS"
else
    echo "  ✗ Ingress not found!"
fi
echo ""

# ─── Test 7: Test HTTP access ───
echo "✓ Testing HTTP access to $HOST..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://$HOST" || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "302" ]; then
    echo "  → HTTP $HTTP_CODE - WordPress responding"
else
    echo "  ✗ HTTP $HTTP_CODE - Not accessible"
    echo "  → Make sure /etc/hosts has: 127.0.0.1 $HOST"
fi
echo ""

# ─── Test 8: Check WooCommerce plugin ───
echo "✓ Checking WooCommerce plugin..."
WP_POD=$(kubectl get pod -n "$NAMESPACE" -l app.kubernetes.io/component=wordpress -o jsonpath='{.items[0].metadata.name}')
if [ -n "$WP_POD" ]; then
    WOO_STATUS=$(kubectl exec -n "$NAMESPACE" "$WP_POD" -- wp plugin is-installed woocommerce --path=/var/www/html 2>&1)
    if echo "$WOO_STATUS" | grep -q "Success"; then
        echo "  → WooCommerce plugin is installed"
        
        # Check if active
        WOO_ACTIVE=$(kubectl exec -n "$NAMESPACE" "$WP_POD" -- wp plugin list --path=/var/www/html --format=json | grep -o '"name":"woocommerce","status":"active"' || echo "")
        if [ -n "$WOO_ACTIVE" ]; then
            echo "  → WooCommerce is active ✓"
        else
            echo "  ⚠ WooCommerce is installed but not active"
        fi
    else
        echo "  ✗ WooCommerce plugin not found!"
    fi
else
    echo "  ✗ Could not find WordPress pod"
fi
echo ""

# ─── Test 9: Check WooCommerce pages ───
echo "✓ Testing WooCommerce endpoints..."
SHOP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://$HOST/shop" || echo "000")
CART_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://$HOST/cart" || echo "000")
CHECKOUT_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://$HOST/checkout" || echo "000")

echo "  → Shop page: HTTP $SHOP_CODE"
echo "  → Cart page: HTTP $CART_CODE"
echo "  → Checkout page: HTTP $CHECKOUT_CODE"
echo ""

# ─── Summary ───
echo "════════════════════════════════════════════════════════════════"
echo "Test Summary"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "WordPress URL:     http://$HOST"
echo "Admin panel:       http://$HOST/wp-admin"
echo "WooCommerce Shop:  http://$HOST/shop"
echo ""
echo "To view logs:"
echo "  kubectl logs -n $NAMESPACE -l app.kubernetes.io/component=wordpress"
echo "  kubectl logs -n $NAMESPACE -l app.kubernetes.io/component=wp-setup"
echo ""
echo "To access MySQL:"
echo "  kubectl exec -it -n $NAMESPACE ${STORE_NAME}-mysql-0 -- mysql -u wordpress -p"
echo ""
echo "To run WP-CLI commands:"
echo "  kubectl exec -it -n $NAMESPACE $WP_POD -- wp --path=/var/www/html <command>"
echo ""
