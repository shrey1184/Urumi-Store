# Urumi-Ai: Kubernetes-Native Store Provisioning Platform

**Provision fully-functional WooCommerce and MedusaJS e-commerce stores on-demand** — via a React dashboard backed by a FastAPI orchestrator and Helm charts running on Kubernetes.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Table of Contents

- [What is this?](#-what-is-this)
- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Local Setup (Kind)](#local-setup-kind)
- [Creating a Store & Placing an Order](#creating-a-store--placing-an-order)
  - [WooCommerce](#create-a-woocommerce-store)
  - [MedusaJS](#create-a-medusajs-store)
- [VPS / Production Setup (k3s)](#vps--production-setup-k3s)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Configuration Reference](#configuration-reference)
- [Upgrade & Rollback](#upgrade--rollback)
- [Security](#security)
- [Troubleshooting](#-troubleshooting)
- [Documentation](#-documentation)
- [Contributing](#-contributing)

---

## 🚀 What is this?

A production-grade platform that automates e-commerce store deployment on Kubernetes. Users create stores through a web dashboard, and the system handles the full lifecycle — namespace creation, Helm chart installation, DNS configuration, and clean teardown.

### Supported Store Types

| Store Type | Stack | Status |
|------------|-------|--------|
| **WooCommerce** | WordPress 6.4 + WooCommerce + MySQL 8.0 | ✅ Fully Implemented |
| **MedusaJS** | Medusa v2 + PostgreSQL 15 + Redis 7 + Next.js Storefront | ✅ Fully Implemented |

### Key Features

- 🎯 **One-click store creation** — React UI triggers automated Helm deployments
- ⚡ **Background provisioning** — FastAPI handles async orchestration (2-4 min per store)
- 🔒 **Multi-tenant isolation** — Each store gets its own Kubernetes namespace with ResourceQuota & LimitRange
- 🛠️ **Full lifecycle management** — Create, monitor, and delete stores via REST API
- 🧹 **Clean teardown** — Helm uninstall + namespace deletion removes all resources
- 📊 **Real-time monitoring** — Dashboard polls for status with pod-level detail
- 🔑 **Secure secrets** — Passwords generated at runtime, never hardcoded, stored as K8s Secrets
- 🏗️ **Production-ready** — Readiness/liveness probes, resource limits, RBAC, and Helm values for local vs prod

---

## Architecture Overview

```
 ┌─────────────────┐     ┌──────────────────┐     ┌────────────────────────────────────┐
 │  React Dashboard │────▶│  FastAPI Backend  │────▶│      Kubernetes Cluster            │
 │  (Vite + React)  │     │  (Orchestrator)   │     │      (Kind / k3s)                  │
 │  port 5173       │     │  port 8000        │     │                                    │
 └─────────────────┘     └──────────────────┘     │  ┌──────────────────────────────┐   │
                               │                    │  │ store-myshop (WooCommerce)   │   │
                               │ Helm install /     │  │  ├─ WordPress (Deployment)   │   │
                               │ uninstall          │  │  ├─ MySQL (StatefulSet+PVC)  │   │
                               │ + K8s API          │  │  ├─ WP-CLI Init Job          │   │
                               └───────────────────▶│  │  ├─ Ingress (subdomain)      │   │
                                                    │  │  ├─ Secrets                   │   │
                                                    │  │  └─ ResourceQuota+LimitRange │   │
                                                    │  └──────────────────────────────┘   │
                                                    │  ┌──────────────────────────────┐   │
                                                    │  │ store-demo (MedusaJS)        │   │
                                                    │  │  ├─ Medusa API (Deployment)  │   │
                                                    │  │  ├─ PostgreSQL (SS+PVC)      │   │
                                                    │  │  ├─ Redis (Deployment)       │   │
                                                    │  │  ├─ Storefront/Next.js       │   │
                                                    │  │  ├─ Medusa Init Job          │   │
                                                    │  │  ├─ Ingress (subdomain)      │   │
                                                    │  │  └─ ResourceQuota+LimitRange │   │
                                                    │  └──────────────────────────────┘   │
                                                    └────────────────────────────────────┘
```

### Components

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| **Dashboard** | React 19 + Vite 7 | UI for creating/viewing/deleting stores with real-time status |
| **API** | FastAPI (Python 3.11+) | REST API, store CRUD, background orchestration, health monitoring |
| **Orchestrator** | Python + kubernetes-client + Helm CLI | Creates namespaces, applies quotas, installs Helm charts, manages DNS |
| **WooCommerce Chart** | Helm | WordPress + WooCommerce + MySQL + WP-CLI init + Ingress + Probes |
| **MedusaJS Chart** | Helm | Medusa + PostgreSQL + Redis + Next.js Storefront + Init Job + Ingress |
| **Platform Chart** | Helm | Deploys the API + Dashboard onto K8s with RBAC |

> 📖 For detailed architecture, data flows, and design decisions, see [Docs/ARCHITECTURE.md](Docs/ARCHITECTURE.md).

---

## Prerequisites

Before you begin, ensure you have the following installed:

| Tool | Minimum Version | Purpose | Install Link |
|------|----------------|---------|-------------|
| **Docker** | 20.10+ | Container runtime | [Install](https://docs.docker.com/get-docker/) |
| **Kind** | 0.20+ | Local Kubernetes cluster | [Install](https://kind.sigs.k8s.io/docs/user/quick-start/#installation) |
| **kubectl** | 1.24+ | Kubernetes CLI | [Install](https://kubernetes.io/docs/tasks/tools/) |
| **Helm** | 3.8+ | Chart management | [Install](https://helm.sh/docs/intro/install/) |
| **Python** | 3.11+ | Backend API | [Install](https://www.python.org/downloads/) |
| **Node.js** | 18+ | Frontend dashboard | [Install](https://nodejs.org/) |

<details>
<summary>📦 Quick install commands (Linux / macOS)</summary>

```bash
# ─── macOS (Homebrew) ───
brew install kind kubectl helm python@3.11 node

# ─── Linux (Ubuntu/Debian) ───

# Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Python 3.11+
sudo apt update && sudo apt install -y python3.11 python3.11-venv python3-pip

# Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```
</details>

### Verify Prerequisites

```bash
docker --version     # Docker version 20.10+
kind --version       # kind v0.20+
kubectl version --client  # v1.24+
helm version         # v3.8+
python3 --version    # Python 3.11+
node --version       # v18+
```

---

## Local Setup (Kind)

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-username/Urumi-Ai.git
cd Urumi-Ai
```

### Step 2: Create the Kubernetes Cluster

```bash
chmod +x scripts/*.sh
./scripts/setup-local.sh
```

This script:
- ✅ Creates a Kind cluster named `store-platform` with ports 80/443 mapped to localhost
- ✅ Installs the NGINX Ingress Controller
- ✅ Creates the `store-platform` namespace
- ✅ Waits for the ingress controller to be fully ready

### Step 3: Start the Backend API

```bash
cd Backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO | Starting Store Provisioning Platform
INFO | ✓ Successfully connected to Kubernetes
INFO | K8s connected: True
INFO | Uvicorn running on http://0.0.0.0:8000
```

### Step 4: Start the Frontend Dashboard

```bash
# In a new terminal
cd Frontend
npm install
npm run dev
```

### Step 5: Access the Dashboard

Open **http://localhost:5173** in your browser.

### Step 6: DNS Setup for Store URLs (One-Time Setup)

When you create stores, they'll be accessible at URLs like `http://storename.local.store.dev`. 

**Run this once to enable automatic DNS resolution:**

```bash
cd /home/shrey/Urumi-Ai
./scripts/setup-hosts-manager.sh
```

This configures:
- ✅ Automatic `/etc/hosts` updates when stores are created
- ✅ Passwordless sudo for the hosts file manager
- ✅ Syncs all existing store domains

**Now you can create stores and immediately access them in your browser!**

> 📖 For troubleshooting DNS issues, see [Docs/DNS_SETUP.md](Docs/DNS_SETUP.md)

**Alternative: If you prefer manual management:**

```bash
# Add manually after creating a store
echo "127.0.0.1  my-shop.local.store.dev" | sudo tee -a /etc/hosts

# Or sync all stores at once
./scripts/update-hosts.sh sync
```

---

## Creating a Store & Placing an Order

### Create a WooCommerce Store

1. Open the dashboard at **http://localhost:5173**
2. Click the **"Create Store"** button
3. Enter a store name (e.g., `my-shop`) — must be lowercase, alphanumeric, hyphens allowed
4. Select **WooCommerce** as the store type
5. Click **Create**
6. Watch the status transition: **Provisioning** → **Ready** (typically 2-4 minutes)
7. Once ready, the store URL and admin URL appear on the store card

### Place an Order (WooCommerce)

1. Click the **store URL** (e.g., `http://my-shop.local.store.dev`)
2. Browse to the **Shop** page — a **Sample Product** is pre-created by the WP-CLI init job
3. Click **Add to Cart** → **View Cart** → **Proceed to Checkout**
4. Fill in billing details (any test data)
5. Select **Cash on Delivery** as the payment method
6. Click **Place Order**
7. **Verify** in WP Admin:
   - Go to `http://my-shop.local.store.dev/wp-admin`
   - Login with the credentials shown on the dashboard store card
   - Navigate to **WooCommerce → Orders** to see the placed order

### Create a MedusaJS Store

1. Open the dashboard at **http://localhost:5173**
2. Click the **"Create Store"** button
3. Enter a store name (e.g., `demo-store`)
4. Select **MedusaJS** as the store type
5. Click **Create**
6. Wait for **Provisioning** → **Ready** (typically 3-5 minutes — includes PostgreSQL init, Redis, and Medusa seed)
7. Once ready:
   - **Storefront**: `http://demo-store.local.store.dev` (Next.js storefront)
   - **Admin Panel**: `http://demo-store.local.store.dev/admin` (Medusa admin dashboard)
   - **API**: `http://demo-store.local.store.dev/store/products` (REST API)

### Place an Order (MedusaJS)

1. Open the **storefront URL** (`http://demo-store.local.store.dev`)
2. Browse products (seeded during init)
3. Add items to cart
4. Proceed through checkout flow
5. **Verify** in Medusa Admin:
   - Go to `http://demo-store.local.store.dev/admin`
   - Login with the admin credentials from the dashboard
   - Navigate to **Orders** to see the placed order

### Running Multiple Stores Concurrently

You can run WooCommerce and MedusaJS stores side by side:

```bash
# Create both stores
curl -X POST http://localhost:8000/api/v1/stores \
  -H "Content-Type: application/json" \
  -d '{"name": "woo-store", "store_type": "woocommerce"}'

curl -X POST http://localhost:8000/api/v1/stores \
  -H "Content-Type: application/json" \
  -d '{"name": "medusa-store", "store_type": "medusa"}'

# List all stores
curl http://localhost:8000/api/v1/stores | python3 -m json.tool

# Check resources per store
kubectl get all -n store-woo-store
kubectl get all -n store-medusa-store
```

### Delete a Store

1. In the dashboard, click the **Delete** button (trash icon) on the store card
2. Confirm the deletion in the popup
3. The system:
   - Sets status to **Deleting**
   - Runs `helm uninstall` to remove all chart resources
   - Deletes the entire Kubernetes namespace (safety net — removes everything)
   - Removes the `/etc/hosts` entry (local mode)
   - Deletes the database record

Verify cleanup:
```bash
kubectl get ns | grep store-    # Namespace should be gone
kubectl get all -n store-<name> # Should return "not found"
```

---

## VPS / Production Setup (k3s)

### Step 1: Install k3s on your VPS

```bash
# SSH into your VPS
ssh user@your-vps-ip

# Clone the repo
git clone https://github.com/your-username/Urumi-Ai.git
cd Urumi-Ai

# Run the setup script
./scripts/setup-prod.sh
```

This installs k3s (lightweight Kubernetes) and configures kubeconfig.

### Step 2: Configure DNS

Point a **wildcard DNS** record to your VPS IP:

```
*.yourdomain.com  →  A  →  <VPS-IP>
```

This allows stores to be accessible at `storename.yourdomain.com` automatically.

### Step 3: Configure Environment

```bash
cd Backend
cat > .env << EOF
BASE_DOMAIN=yourdomain.com
INGRESS_CLASS=traefik
IN_CLUSTER=false
KUBECONFIG=/etc/rancher/k3s/k3s.yaml
DATABASE_URL=sqlite+aiosqlite:///./stores.db
MAX_STORES=50
DEBUG=false
EOF
```

### Step 4: Deploy with Production Values

```bash
# Start the backend
KUBECONFIG=/etc/rancher/k3s/k3s.yaml uvicorn app.main:app --host 0.0.0.0 --port 8000

# Build and serve the frontend
cd Frontend && npm run build
# Serve dist/ with nginx or any static file server
```

### Step 5 (Optional): TLS with cert-manager

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.4/cert-manager.yaml

# Create a ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@yourdomain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: traefik
EOF
```

### Local vs Production Comparison

| Concern | Local (Kind) | Production (k3s VPS) |
|---------|-------------|---------------------|
| **Cluster** | Kind (Docker-in-Docker) | k3s (lightweight K8s) |
| **Ingress class** | `nginx` | `traefik` (k3s built-in) |
| **Domain** | `local.store.dev` + `/etc/hosts` | Real domain with wildcard DNS |
| **TLS** | None / self-signed | cert-manager + Let's Encrypt |
| **Storage class** | `standard` | `local-path` |
| **Database** | SQLite | PostgreSQL (swap via `DATABASE_URL`) |
| **Resources** | Minimal (dev) | Production limits in `values-prod.yaml` |

---

## Project Structure

```
Urumi-Ai/
├── Backend/                          # FastAPI Backend
│   ├── app/
│   │   ├── main.py                   # FastAPI entry point, CORS, lifespan
│   │   ├── config.py                 # Pydantic settings (all from env vars)
│   │   ├── database.py               # SQLAlchemy async engine (SQLite / PostgreSQL)
│   │   ├── models.py                 # Store ORM model (id, name, type, status, URLs)
│   │   ├── schemas.py                # Pydantic request/response validation
│   │   ├── routes.py                 # API endpoints (health, stores CRUD, pods)
│   │   ├── orchestrator.py           # Store lifecycle (create→provision→ready→delete)
│   │   ├── k8s_client.py             # Kubernetes client (namespace, quota, secrets, pods)
│   │   └── helm_client.py            # Async Helm CLI wrapper (install, upgrade, rollback)
│   ├── Dockerfile                    # Multi-stage Python container
│   ├── requirements.txt              # Python dependencies
│   └── pyproject.toml                # Python project metadata
│
├── Frontend/                         # React Dashboard
│   ├── src/
│   │   ├── App.jsx                   # Root component with toast notifications
│   │   ├── main.jsx                  # React DOM entry point
│   │   ├── api.js                    # Axios HTTP client for backend API
│   │   ├── config.js                 # API base URL configuration
│   │   ├── pages/
│   │   │   └── Dashboard.jsx         # Main page: store list, stats, polling
│   │   └── components/
│   │       ├── CreateStoreModal.jsx   # Modal form for WooCommerce / MedusaJS
│   │       ├── StoreCard.jsx          # Store card with status, URLs, delete
│   │       └── StatusBar.jsx          # Kubernetes connection health bar
│   ├── Dockerfile                    # Nginx-based production container
│   ├── nginx.conf                    # Nginx reverse proxy config
│   └── package.json                  # Node.js dependencies
│
├── helm/                             # Helm Charts
│   ├── platform/                     # Platform chart (API + Dashboard on K8s)
│   │   ├── Chart.yaml
│   │   ├── values.yaml
│   │   └── templates/
│   │       ├── api.yaml              # API Deployment + Service
│   │       ├── dashboard.yaml        # Dashboard Deployment + Service
│   │       ├── ingress.yaml          # Platform ingress
│   │       └── rbac.yaml             # ServiceAccount + ClusterRole + Binding
│   │
│   ├── woocommerce/                  # WooCommerce store chart
│   │   ├── Chart.yaml
│   │   ├── values.yaml               # Default values
│   │   ├── values-local.yaml         # Kind-specific overrides
│   │   ├── values-prod.yaml          # Production overrides (k3s + TLS)
│   │   └── templates/
│   │       ├── wordpress-deployment.yaml
│   │       ├── wordpress-service.yaml
│   │       ├── mysql-statefulset.yaml
│   │       ├── mysql-service.yaml
│   │       ├── wp-setup-job.yaml     # WP-CLI: install WordPress + WooCommerce
│   │       ├── ingress.yaml          # Per-store subdomain routing
│   │       ├── secrets.yaml          # Admin + DB credentials
│   │       └── pvc.yaml              # Persistent storage
│   │
│   └── medusa/                       # MedusaJS store chart
│       ├── Chart.yaml
│       ├── values.yaml               # Default values
│       ├── values-local.yaml         # Kind-specific overrides
│       ├── values-prod.yaml          # Production overrides
│       └── templates/
│           ├── medusa-deployment.yaml # Medusa backend (Node.js :9000)
│           ├── medusa-service.yaml
│           ├── medusa-init-job.yaml   # DB migrations + seed + admin user
│           ├── postgres-statefulset.yaml
│           ├── postgres-service.yaml
│           ├── redis-deployment.yaml
│           ├── redis-service.yaml
│           ├── storefront-deployment.yaml  # Next.js storefront (:8000)
│           ├── storefront-service.yaml
│           ├── ingress.yaml           # Per-store subdomain routing
│           ├── secrets.yaml           # Admin, DB, JWT, cookie secrets
│           └── pvc.yaml               # PostgreSQL persistent storage
│
├── scripts/                          # Infrastructure scripts
│   ├── setup-local.sh                # Create Kind cluster + NGINX Ingress
│   ├── setup-prod.sh                 # Install k3s on VPS
│   ├── teardown-local.sh             # Delete Kind cluster
│   ├── load-images-to-kind.sh        # Load Docker images into Kind
│   └── ingress-controller.yaml       # NGINX Ingress Controller manifests
│
├── Docs/                             # Documentation
│   ├── ARCHITECTURE.md               # System design, data flows, tradeoffs
│   ├── SYSTEM_DESIGN.md              # Architecture decisions & security
│   └── ...
│
├── README.md                         # This file
├── CONTRIBUTING.md                   # Contribution guidelines
├── CHANGELOG.md                      # Version history
└── LICENSE                           # MIT License
```

---

## API Reference

### Endpoints

| Method | Endpoint | Description | Status Codes |
|--------|----------|-------------|-------------|
| `GET` | `/api/v1/health` | Health check + K8s connection status | 200 |
| `GET` | `/api/v1/stores` | List all stores with status | 200 |
| `GET` | `/api/v1/stores/{id}` | Get single store details | 200, 404 |
| `POST` | `/api/v1/stores` | Create a new store (async provisioning) | 201, 409, 429 |
| `DELETE` | `/api/v1/stores/{id}` | Delete a store (async teardown) | 200, 404, 409 |
| `GET` | `/api/v1/stores/{id}/pods` | List Kubernetes pods for a store | 200, 404 |

### Request / Response Examples

<details>
<summary><b>POST /api/v1/stores</b> — Create a store</summary>

**Request:**
```json
{
  "name": "my-shop",
  "store_type": "woocommerce"
}
```

**Validation rules:**
- `name`: 2-50 chars, lowercase alphanumeric + hyphens, must start/end with alphanumeric
- `store_type`: `"woocommerce"` or `"medusa"`

**Response (201):**
```json
{
  "id": "a1b2c3d4-...",
  "name": "my-shop",
  "store_type": "woocommerce",
  "status": "provisioning",
  "namespace": "store-my-shop",
  "store_url": null,
  "admin_url": null,
  "error_message": null,
  "created_at": "2026-02-13T10:00:00Z",
  "updated_at": "2026-02-13T10:00:00Z"
}
```

**Error (409):** `{"detail": "Store with name 'my-shop' already exists"}`  
**Error (429):** `{"detail": "Maximum number of stores (10) reached"}`
</details>

<details>
<summary><b>GET /api/v1/stores</b> — List stores</summary>

**Response (200):**
```json
{
  "stores": [
    {
      "id": "a1b2c3d4-...",
      "name": "my-shop",
      "store_type": "woocommerce",
      "status": "ready",
      "namespace": "store-my-shop",
      "store_url": "https://my-shop.local.store.dev",
      "admin_url": "https://my-shop.local.store.dev/wp-admin",
      "error_message": null,
      "created_at": "2026-02-13T10:00:00Z",
      "updated_at": "2026-02-13T10:03:00Z"
    }
  ],
  "total": 1
}
```
</details>

<details>
<summary><b>GET /api/v1/health</b> — Health check</summary>

**Response (200):**
```json
{
  "status": "ok",
  "kubernetes_connected": true,
  "version": "1.0.0"
}
```
</details>

<details>
<summary><b>GET /api/v1/stores/{id}/pods</b> — Pod inspection</summary>

**Response (200):**
```json
{
  "store_id": "a1b2c3d4-...",
  "namespace": "store-my-shop",
  "pods": [
    {"name": "my-shop-wordpress-abc123", "status": "Running", "ready": true},
    {"name": "my-shop-mysql-0", "status": "Running", "ready": true}
  ]
}
```
</details>

---

## Configuration Reference

All configuration is via **environment variables** (or `.env` file in the Backend directory):

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `true` | Enable debug logging |
| `DATABASE_URL` | `sqlite+aiosqlite:///./stores.db` | Database connection string |
| `KUBECONFIG` | `~/.kube/config` | Path to kubeconfig file |
| `IN_CLUSTER` | `false` | Set `true` when running inside Kubernetes |
| `HELM_BINARY` | `helm` | Path to Helm binary |
| `BASE_DOMAIN` | `local.store.dev` | Base domain for store subdomains |
| `INGRESS_CLASS` | `nginx` | Kubernetes ingress class |
| `MAX_STORES` | `10` | Maximum number of concurrent stores |
| `PROVISION_TIMEOUT_SECONDS` | `600` | Helm install timeout (seconds) |
| `RATE_LIMIT_PER_MINUTE` | `10` | API rate limit per minute |
| `NAMESPACE_PREFIX` | `store-` | Prefix for store Kubernetes namespaces |

---

## Upgrade & Rollback

### Upgrade a Store's Helm Chart

```bash
# Upgrade WordPress version
helm upgrade my-shop helm/woocommerce/ \
  --namespace store-my-shop \
  --set wordpress.image=wordpress:6.5-apache \
  --reuse-values

# Upgrade Medusa store
helm upgrade demo-store helm/medusa/ \
  --namespace store-demo-store \
  --reuse-values
```

### Rollback

```bash
# Rollback to the previous release
helm rollback my-shop --namespace store-my-shop

# Rollback to a specific revision
helm rollback my-shop 2 --namespace store-my-shop

# View release history
helm history my-shop --namespace store-my-shop
```

### Zero-Downtime Upgrade Strategy

- Deployments use `RollingUpdate` strategy — new pods start before old ones terminate
- StatefulSets use `OnDelete` strategy for safety (databases)
- `helm upgrade --wait` ensures new pods are Ready before marking complete
- Readiness probes prevent traffic routing to unready pods

---

## Security

### Secrets Management
- Passwords are **generated at runtime** using Python `secrets` module (cryptographically secure)
- Secrets are passed to Helm via `--set` flags — **never written to temporary files**
- Stored as Kubernetes `Secret` resources (base64 in etcd, encrypted at rest if configured)
- No hardcoded secrets anywhere in source code

### RBAC (Least Privilege)
- Platform ServiceAccount has a scoped ClusterRole with only necessary permissions
- No `cluster-admin` privileges
- Scoped to: namespaces, pods, services, PVCs, secrets, deployments, statefulsets, ingresses, jobs, resource quotas

### Network Isolation
- Database services (MySQL, PostgreSQL, Redis) are **ClusterIP only** — unreachable from outside the cluster
- Only Ingress resources expose storefronts publicly

### Input Validation
- Store names: strict regex `^[a-z0-9][a-z0-9\-]*[a-z0-9]$` — DNS-safe, injection-proof
- Store type: enum-validated (`woocommerce` or `medusa`)
- Max store limit enforced at API level

> 📖 For detailed security analysis, see [Docs/ARCHITECTURE.md](Docs/ARCHITECTURE.md#security-considerations).

---

## 🐛 Troubleshooting

<details>
<summary><b>Store stuck in "Provisioning" state</b></summary>

**Check backend logs** (the terminal running uvicorn):
```bash
# Look for Helm errors or K8s API failures in the output
```

**Check if the namespace was created:**
```bash
kubectl get ns | grep store-
```

**Check pods in the store namespace:**
```bash
kubectl get pods -n store-<store-name>
kubectl describe pod <pod-name> -n store-<store-name>
kubectl logs <pod-name> -n store-<store-name>
```

**Common causes:**
- Image pull failures (check Docker Hub rate limits)
- Insufficient cluster resources
- Helm chart template errors

**Recovery:** Delete the store and retry:
```bash
curl -X DELETE http://localhost:8000/api/v1/stores/<store-id>
```
</details>

<details>
<summary><b>Can't access store URL (connection refused)</b></summary>

1. **Check `/etc/hosts`** has the entry:
   ```bash
   grep "local.store.dev" /etc/hosts
   # Should show: 127.0.0.1  <store-name>.local.store.dev
   ```

2. **Verify Ingress is created:**
   ```bash
   kubectl get ingress -n store-<store-name>
   kubectl describe ingress -n store-<store-name>
   ```

3. **Check NGINX Ingress Controller is running:**
   ```bash
   kubectl get pods -n ingress-nginx
   # All pods should be Running + Ready
   ```

4. **Check if ports 80/443 are mapped:**
   ```bash
   docker port store-platform-control-plane
   # Should show 80/tcp -> 0.0.0.0:80
   ```
</details>

<details>
<summary><b>Kubernetes connection failed (backend startup)</b></summary>

1. **Verify cluster is running:**
   ```bash
   kind get clusters
   kubectl cluster-info
   kubectl get nodes
   ```

2. **Check kubeconfig is accessible:**
   ```bash
   echo $KUBECONFIG
   cat ~/.kube/config | head -5
   ```

3. **Recreate the cluster:**
   ```bash
   ./scripts/teardown-local.sh
   ./scripts/setup-local.sh
   ```
</details>

<details>
<summary><b>MySQL / PostgreSQL pod CrashLoopBackOff</b></summary>

```bash
# Check pod events
kubectl describe pod <mysql-pod> -n store-<name>

# Check logs
kubectl logs <mysql-pod> -n store-<name>

# Common fix: PVC might be corrupted, delete and recreate store
curl -X DELETE http://localhost:8000/api/v1/stores/<store-id>
```
</details>

<details>
<summary><b>Helm install timeout</b></summary>

The default timeout is 600 seconds (10 minutes). If pods take longer to start:

```bash
# Check what's pending
kubectl get pods -n store-<name> -w

# Increase timeout in .env
PROVISION_TIMEOUT_SECONDS=900
```

Common causes: slow image pulls on first run, insufficient resources.
</details>

<details>
<summary><b>Port 80 already in use</b></summary>

```bash
# Find what's using port 80
sudo lsof -i :80

# Stop the conflicting service, or use a different Kind config
# with alternative port mappings
```
</details>

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Docs/ARCHITECTURE.md](Docs/ARCHITECTURE.md) | System design, component diagram, data flows, isolation strategy, security, scaling |
| [Docs/SYSTEM_DESIGN.md](Docs/SYSTEM_DESIGN.md) | Architecture decisions, tradeoffs, production considerations |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Development setup and contribution guidelines |
| [CHANGELOG.md](CHANGELOG.md) | Version history and release notes |
| [FIX_INGRESS.md](FIX_INGRESS.md) | Ingress troubleshooting guide |

---

## 🤝 Contributing

Contributions are welcome! Please read the [Contributing Guide](CONTRIBUTING.md) first.

```bash
# Fork and clone
git clone https://github.com/<your-username>/Urumi-Ai.git
cd Urumi-Ai

# Set up local cluster
./scripts/setup-local.sh

# Backend development
cd Backend && python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend development
cd Frontend && npm install && npm run dev

# Create a feature branch
git checkout -b feature/my-feature
# ... make changes, test locally, submit PR
```

---

## 📝 Roadmap

- [ ] Comprehensive test coverage (pytest + Jest)
- [ ] Prometheus metrics + Grafana dashboards
- [ ] NetworkPolicies (deny-by-default per namespace)
- [ ] Store backup/restore functionality
- [ ] Custom domain linking per store
- [ ] CI/CD pipeline with GitHub Actions
- [ ] Webhook notifications (Slack / Discord)
- [ ] Multi-cluster support
- [ ] Store cloning functionality
- [ ] HPA for platform API

---

## ⚠️ Known Limitations

| Limitation | Workaround |
|-----------|-----------|
| **SQLite** doesn't support concurrent writes | Use PostgreSQL in production (`DATABASE_URL` env var) |
| **No TLS** in local setup | Use cert-manager + Let's Encrypt for production |
| **Single cluster** only | Multi-cluster support planned |
| **In-memory provisioning locks** | Lost on API restart; stores stay in "provisioning" — delete and retry |
| **Manual DNS** (local mode) | Use nip.io (`BASE_DOMAIN=127.0.0.1.nip.io`) or dnsmasq |
| **No persistent task queue** | Background tasks run in-process; for HA use Celery + Redis |

---

## License

MIT License — See [LICENSE](LICENSE) for details.

**Built with ❤️ by Shrey**
