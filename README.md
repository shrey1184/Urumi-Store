# Urumi-Ai: Kubernetes-Native Store Provisioning Platform

**Provision fully-functional ecommerce stores on-demand** — WooCommerce or MedusaJS — via a React dashboard backed by a FastAPI orchestrator and Helm charts running on Kubernetes.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 What is this?

A production-grade platform that automates ecommerce store deployment on Kubernetes:

- 🎯 **Create stores in one click** — React UI triggers automated Helm deployments
- ⚡ **Background provisioning** — FastAPI handles async orchestration
- 🔒 **Multi-tenant isolation** — Each store gets its own namespace with resource quotas
- 🛠️ **Full lifecycle management** — Create, monitor, and delete stores via REST API
- 🎨 **Two store types** — WooCommerce (WordPress + MySQL) or MedusaJS (Node + PostgreSQL + Redis)

---

## Architecture Overview

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────────┐
│  React Dashboard │────▶│  FastAPI Backend  │────▶│  Kubernetes Cluster  │
│  (Vite + React)  │     │  (Orchestrator)   │     │  (Kind / k3s)        │
│  port 5173       │     │  port 8000        │     │                      │
└─────────────────┘     └──────────────────┘     │  ┌──────────────────┐ │
                              │                    │  │ store-myshop     │ │
                              │  Helm install/     │  │  ├ WordPress     │ │
                              │  uninstall         │  │  ├ MySQL         │ │
                              └───────────────────▶│  │  ├ Ingress       │ │
                                                   │  │  └ PVCs          │ │
                                                   │  └──────────────────┘ │
                                                   │  ┌──────────────────┐ │
                                                   │  │ store-other      │ │
                                                   │  │  ├ Medusa        │ │
                                                   │  │  ├ PostgreSQL    │ │
                                                   │  │  ├ Redis         │ │
                                                   │  │  └ Ingress       │ │
                                                   │  └──────────────────┘ │
                                                   └──────────────────────┘
```

### Components

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| **Dashboard** | React + Vite | UI for creating/viewing/deleting stores |
| **API** | FastAPI (Python) | REST API, store CRUD, background orchestration |
| **Orchestrator** | Python + kubernetes-client + Helm CLI | Creates namespaces, installs Helm charts, manages lifecycle |
| **WooCommerce Chart** | Helm | WordPress + MySQL + WP-CLI setup job + Ingress |
| **MedusaJS Chart** | Helm | Medusa + PostgreSQL + Redis + Ingress |
| **Platform Chart** | Helm | Deploys the dashboard + API onto K8s |

---

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** (20.10+ recommended) — [Install docs](https://docs.docker.com/get-docker/)
- **Kind** — `go install sigs.k8s.io/kind@latest` or [install docs](https://kind.sigs.k8s.io/docs/user/quick-start/#installation)
- **kubectl** (1.24+) — [Install docs](https://kubernetes.io/docs/tasks/tools/)
- **Helm 3** (3.8+) — [Install docs](https://helm.sh/docs/intro/install/)
- **Python 3.11+** — For the backend API
- **Node.js 18+** — For the frontend dashboard

<details>
<summary>📦 Quick install commands</summary>

```bash
# macOS (Homebrew)
brew install kind kubectl helm python@3.11 node

# Linux (Ubuntu/Debian)
# Kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64
chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl && sudo mv kubectl /usr/local/bin/

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```
</details>

---

## 🎯 Features

### Core Capabilities
✅ **One-click store creation** — WooCommerce stores ready in 2-4 minutes  
✅ **Multi-tenant isolation** — Each store in its own namespace with resource limits  
✅ **Automatic DNS** — Stores accessible via subdomain (e.g., `myshop.local.store.dev`)  
✅ **Resource quotas** — CPU, memory, and storage limits per store  
✅ **Background provisioning** — Non-blocking async orchestration  
✅ **Clean teardown** — Complete resource cleanup on delete  
✅ **Real-time status** — Monitor provisioning progress from the dashboard  
✅ **Pod inspection** — View running containers per store  

### Technical Highlights
- **FastAPI** backend with async/await throughout
- **SQLite** for metadata (PostgreSQL-ready via env var)
- **Helm CLI** integration for templating and lifecycle management
- **Kubernetes Python client** for namespace/resource management
- **React + Vite** frontend with modern UI
- **NGINX Ingress** for routing (Traefik support for k3s)

---

## Local Setup (Kind)

### 1. Create the Kubernetes cluster

```bash
chmod +x scripts/*.sh
./scripts/setup-local.sh
```

This creates a Kind cluster with:
- Ingress-ready node (ports 80/443 mapped to host)
- NGINX Ingress Controller installed
- `store-platform` namespace created

### 2. Start the Backend

```bash
cd Backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy env file
cp .env.example .env

# Start the server
uvicorn app.main:app --reload --port 8000
```

### 3. Start the Frontend

```bash
cd Frontend
npm install
npm run dev
```

### 4. Access the Dashboard

Open **http://localhost:5173** in your browser.

### 5. DNS Setup for Store URLs

When you create a store (e.g., `my-shop`), it will be accessible at `http://my-shop.local.store.dev`.

Add to `/etc/hosts`:
```
127.0.0.1  my-shop.local.store.dev
```

Or use **nip.io** for automatic DNS (set `BASE_DOMAIN=127.0.0.1.nip.io` in `.env`).

---

## Creating a Store & Placing an Order

### Create a WooCommerce Store

1. Open the dashboard at http://localhost:5173
2. Click **"Create Store"**
3. Enter a name (e.g., `my-shop`) and select **WooCommerce**
4. Wait for status to change from "Provisioning" → "Ready" (2-4 minutes)
5. Click the store URL to open the storefront

### Place an Order (WooCommerce)

1. Open the store URL (e.g., `http://my-shop.local.store.dev`)
2. Browse products → **"Sample Product"** is pre-created
3. Add to cart → Proceed to checkout
4. Fill in billing details, select **Cash on Delivery**
5. Place order
6. Verify in WP Admin (`/wp-admin`, credentials shown in dashboard) → WooCommerce → Orders

### Delete a Store

1. In the dashboard, click **Delete** on the store card
2. Confirm deletion
3. The system uninstalls the Helm release + deletes the entire namespace (all resources cleaned up)

---

## VPS / Production Setup (k3s)

### 1. Install k3s on your VPS

```bash
./scripts/setup-prod.sh
```

### 2. What changes via Helm values

| Concern | Local (Kind) | Production (k3s VPS) |
|---------|-------------|---------------------|
| **Ingress class** | `nginx` | `traefik` (k3s default) |
| **Domain** | `local.store.dev` | Your real domain |
| **Storage class** | `standard` | `local-path` |
| **TLS** | None | cert-manager + Let's Encrypt |
| **Resources** | Minimal | Production limits |

### 3. Deploy with production values

```bash
# Deploy a WooCommerce store with prod values
helm install my-store helm/woocommerce/ \
  -f helm/woocommerce/values-prod.yaml \
  --namespace store-my-store \
  --create-namespace \
  --set storeName=my-store \
  --set baseDomain=yourdomain.com \
  --set wordpress.adminPassword=<secure-password> \
  --set mysql.rootPassword=<secure-password> \
  --set mysql.password=<secure-password>
```

### 4. TLS with cert-manager (optional)

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.14.4/cert-manager.yaml

# Create a ClusterIssuer for Let's Encrypt
# (see values-prod.yaml for ingress annotations)
```

---

## Project Structure

```
├── Backend/
│   ├── app/
│   │   ├── main.py            # FastAPI entry point
│   │   ├── config.py          # Settings from env vars
│   │   ├── database.py        # SQLAlchemy async setup
│   │   ├── models.py          # Store model (SQLite)
│   │   ├── schemas.py         # Pydantic request/response models
│   │   ├── routes.py          # API endpoints (CRUD)
│   │   ├── orchestrator.py    # Store lifecycle management
│   │   ├── k8s_client.py      # Kubernetes API wrapper
│   │   └── helm_client.py     # Helm CLI async wrapper
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── Frontend/
│   ├── src/
│   │   ├── App.jsx            # Main app with toast notifications
│   │   ├── api.js             # Axios API client
│   │   ├── config.js          # API base URL config
│   │   ├── pages/
│   │   │   └── Dashboard.jsx  # Main dashboard page
│   │   └── components/
│   │       ├── StoreCard.jsx       # Store status card
│   │       ├── CreateStoreModal.jsx # Store creation form
│   │       └── StatusBar.jsx       # K8s connection status
│   ├── Dockerfile
│   └── nginx.conf
├── helm/
│   ├── platform/              # Platform chart (API + Dashboard)
│   ├── woocommerce/           # WooCommerce store chart
│   │   ├── values.yaml
│   │   ├── values-local.yaml
│   │   ├── values-prod.yaml
│   │   └── templates/
│   └── medusajs/              # MedusaJS store chart (architecture-ready)
│       ├── values.yaml
│       └── templates/
├── scripts/
│   ├── setup-local.sh         # Kind cluster setup
│   ├── setup-prod.sh          # k3s VPS setup
│   └── teardown-local.sh      # Cluster cleanup
└── Docs/
    └── SYSTEM_DESIGN.md       # Architecture & tradeoffs
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check + K8s connection status |
| GET | `/api/v1/stores` | List all stores |
| GET | `/api/v1/stores/{id}` | Get store details |
| POST | `/api/v1/stores` | Create a new store |
| DELETE | `/api/v1/stores/{id}` | Delete a store |
| GET | `/api/v1/stores/{id}/pods` | List pods for a store |

### Create Store Request
```json
{
  "name": "my-shop",
  "store_type": "woocommerce"  // or "medusajs"
}
```

---

## Upgrade & Rollback

```bash
# Upgrade a store's chart
helm upgrade my-store helm/woocommerce/ \
  --namespace store-my-store \
  --set wordpress.image=wordpress:6.5-apache

# Rollback to previous release
helm rollback my-store --namespace store-my-store

# View release history
helm history my-store --namespace store-my-store
```

---

## 📚 Documentation

- **[System Design & Tradeoffs](Docs/SYSTEM_DESIGN.md)** — Architecture decisions, security posture, production considerations
- **[Contributing Guide](CONTRIBUTING.md)** — Development setup and contribution guidelines
- **[API Reference](#api-reference)** — REST API endpoints
- **[Helm Charts](#project-structure)** — WooCommerce and MedusaJS chart structure

---

## 🤝 Contributing

Contributions are welcome! Please read the [Contributing Guide](CONTRIBUTING.md) first.

### Quick Start for Contributors
```bash
# Fork and clone
git clone https://github.com/<your-username>/Urumi-Ai.git
cd Urumi-Ai

# Create feature branch
git checkout -b feature/my-feature

# Make changes, test locally
./scripts/setup-local.sh

# Submit PR
```

---

## 📝 Roadmap

- [ ] Add comprehensive test coverage (pytest + Jest)
- [ ] Implement store update/upgrade functionality
- [ ] Complete MedusaJS store type implementation
- [ ] Add Prometheus metrics and Grafana dashboards
- [ ] Support custom Helm values per store
- [ ] Implement store backup/restore
- [ ] Add webhook notifications (Slack/Discord)
- [ ] CI/CD pipeline with GitHub Actions
- [ ] Multi-cluster support

---

## ⚠️ Known Limitations

- **SQLite limitation**: Not suitable for high concurrency. Use PostgreSQL in production.
- **No TLS in local setup**: Use cert-manager + Let's Encrypt for production.
- **Single cluster only**: Multi-cluster support planned.
- **No persistent sessions**: API restart clears in-memory locks.
- **Manual DNS**: Requires `/etc/hosts` entries unless using nip.io.

---

## 🐛 Troubleshooting

<details>
<summary>Store stuck in "Provisioning" state</summary>

Check backend logs:
```bash
# In Backend terminal
# Look for Helm errors or K8s API failures

# Check if namespace was created
kubectl get ns | grep store-

# Check pods in the namespace
kubectl get pods -n store-<store-name>

# Delete and retry
curl -X DELETE http://localhost:8000/api/v1/stores/<store-id>
```
</details>

<details>
<summary>Can't access store URL</summary>

1. Check `/etc/hosts` has the entry:
   ```
   127.0.0.1  <store-name>.local.store.dev
   ```

2. Verify ingress is created:
   ```bash
   kubectl get ingress -n store-<store-name>
   ```

3. Check NGINX ingress controller is running:
   ```bash
   kubectl get pods -n ingress-nginx
   ```
</details>

<details>
<summary>Kubernetes connection failed</summary>

1. Verify cluster is running:
   ```bash
   kind get clusters
   kubectl cluster-info
   ```

2. Check kubeconfig:
   ```bash
   export KUBECONFIG=~/.kube/config
   kubectl get nodes
   ```

3. Restart the Kind cluster:
   ```bash
   ./scripts/teardown-local.sh
   ./scripts/setup-local.sh
   ```
</details>

---

## License

MIT License - See [LICENSE](LICENSE) for details.

**Built with ❤️ by Shrey**
# Urumi-Store
