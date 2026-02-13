# Architecture — Store Provisioning Platform (Urumi-Ai)

> A Kubernetes-native, multi-tenant e-commerce store provisioning system that deploys **WooCommerce** and **MedusaJS** stores on-demand through a React dashboard and FastAPI orchestrator.

---

## Table of Contents

- [System Design Diagram](#system-design-diagram)
- [Component Responsibilities](#component-responsibilities)
- [Data Flow: Store Lifecycle](#data-flow-store-lifecycle)
  - [Create Flow](#create-flow)
  - [Delete Flow](#delete-flow)
- [Multi-Tenant Isolation Strategy](#multi-tenant-isolation-strategy)
- [Idempotency Strategy](#idempotency-strategy)
- [Failure Handling Approach](#failure-handling-approach)
- [Security Considerations](#security-considerations)
- [Local vs Production Differences](#local-vs-production-differences)
- [Scaling Approach](#scaling-approach)
- [Abuse Prevention](#abuse-prevention)
- [Observability](#observability)
- [Technology Choices & Tradeoffs](#technology-choices--tradeoffs)

---

## System Design Diagram

```
                         ┌──────────────────────────────────────────────────────────────┐
                         │                     KUBERNETES CLUSTER                       │
                         │                   (Kind local / k3s prod)                    │
                         │                                                              │
 ┌─────────────┐  HTTP   │  ┌──────────────────────────────────────┐                    │
 │   Browser    │◄───────┼──┤   NGINX Ingress Controller           │                    │
 │   (User)     │────────┼──┤   (routes *.local.store.dev)         │                    │
 └─────────────┘         │  └──────┬───────────┬──────────┬────────┘                    │
                         │         │           │          │                              │
                         │         ▼           ▼          ▼                              │
                         │  ┌────────────────────────────────────────────────────────┐   │
                         │  │           store-platform (namespace)                   │   │
                         │  │  ┌─────────────┐    ┌──────────────────┐               │   │
                         │  │  │  Dashboard   │    │  Platform API    │               │   │
                         │  │  │  (React/Nginx│    │  (FastAPI)       │               │   │
                         │  │  │  :80)        │    │  :8000           │               │   │
                         │  │  └─────────────┘    └────────┬─────────┘               │   │
                         │  │                              │                          │   │
                         │  │                   ┌──────────┴──────────┐               │   │
                         │  │                   │   Orchestrator      │               │   │
                         │  │                   │   ├─ K8s Client     │               │   │
                         │  │                   │   ├─ Helm Client    │               │   │
                         │  │                   │   └─ DB (SQLite /   │               │   │
                         │  │                   │       PostgreSQL)   │               │   │
                         │  │                   └──────────┬──────────┘               │   │
                         │  └──────────────────────────────┼─────────────────────────┘   │
                         │                                 │                              │
                         │          Helm install /         │     K8s API                  │
                         │          uninstall              │     (namespaces, quotas)     │
                         │                                 │                              │
                         │    ┌─────────────────────────── ▼ ─────────────────────────┐   │
                         │    │                                                       │   │
                         │    │  ┌─────────────────────────┐  ┌────────────────────┐  │   │
                         │    │  │ store-myshop (namespace) │  │ store-demo (ns)    │  │   │
                         │    │  │  ┌───────────────────┐  │  │  ┌──────────────┐  │  │   │
                         │    │  │  │ WordPress/WooCom  │  │  │  │ Medusa API   │  │  │   │
                         │    │  │  │ (Deployment)      │  │  │  │ (Deployment) │  │  │   │
                         │    │  │  ├───────────────────┤  │  │  ├──────────────┤  │  │   │
                         │    │  │  │ MySQL 8.0         │  │  │  │ PostgreSQL   │  │  │   │
                         │    │  │  │ (StatefulSet+PVC) │  │  │  │ (SS + PVC)   │  │  │   │
                         │    │  │  ├───────────────────┤  │  │  ├──────────────┤  │  │   │
                         │    │  │  │ WP-CLI Init Job   │  │  │  │ Redis        │  │  │   │
                         │    │  │  ├───────────────────┤  │  │  │ (Deployment) │  │  │   │
                         │    │  │  │ Ingress (per-store│  │  │  ├──────────────┤  │  │   │
                         │    │  │  │ subdomain routing)│  │  │  │ Storefront   │  │  │   │
                         │    │  │  ├───────────────────┤  │  │  │ (Next.js)    │  │  │   │
                         │    │  │  │ ResourceQuota     │  │  │  ├──────────────┤  │  │   │
                         │    │  │  │ LimitRange        │  │  │  │ Ingress      │  │  │   │
                         │    │  │  │ Secrets           │  │  │  │ Quota+Limits │  │  │   │
                         │    │  │  └───────────────────┘  │  │  └──────────────┘  │  │   │
                         │    │  └─────────────────────────┘  └────────────────────┘  │   │
                         │    │           ... more stores ...                          │   │
                         │    └───────────────────────────────────────────────────────┘   │
                         └──────────────────────────────────────────────────────────────┘
```

---

## Component Responsibilities

### 1. React Dashboard (Frontend)

| Aspect | Detail |
|--------|--------|
| **Technology** | React 19, Vite 7, Axios, Lucide Icons, React Hot Toast |
| **Serves on** | Port `5173` (dev) / Port `80` (nginx container) |
| **Responsibilities** | Create stores via modal form, list all stores with status, delete stores with confirmation, poll for status updates (every 5s), display pod-level details per store, show Kubernetes connection health |

**Key files:**
- `Dashboard.jsx` — main page with store list, stats, and polling logic
- `CreateStoreModal.jsx` — form to create WooCommerce or MedusaJS stores
- `StoreCard.jsx` — displays store name, type, status, URLs, and delete button
- `StatusBar.jsx` — shows Kubernetes connectivity status
- `api.js` — Axios wrapper for all REST API calls

### 2. FastAPI Backend (API + Orchestrator)

| Aspect | Detail |
|--------|--------|
| **Technology** | Python 3.11+, FastAPI, SQLAlchemy (async), aiosqlite / asyncpg, Pydantic v2 |
| **Serves on** | Port `8000` |
| **Responsibilities** | REST API for store CRUD, OAuth authentication (Google), background provisioning via `BackgroundTasks`, Kubernetes namespace/quota management, Helm chart installation, store metadata persistence, health monitoring |

**Key files:**

| File | Role |
|------|------|
| `main.py` | FastAPI app factory, environment-aware CORS, lifespan (DB init + K8s connect + production validation) |
| `config.py` | Pydantic `BaseSettings` — all config from env vars (DB, JWT, OAuth, SMTP, CORS, etc.) |
| `database.py` | SQLAlchemy async engine + session factory (supports SQLite and PostgreSQL) |
| `models.py` | `User` and `Store` ORM models with status enum (provisioning/ready/failed/deleting) |
| `schemas.py` | Pydantic request/response schemas with validation |
| `routes.py` | API endpoints: health, list, get, create, delete, pods (all user-scoped) |
| `auth.py` | JWT token creation/verification, OAuth client factory, `get_current_user` dependency |
| `auth_routes.py` | OAuth login/callback endpoints, user management, CSRF state with TTL |
| `orchestrator.py` | Core lifecycle logic: namespace → quota → helm install → DNS → status update, auto-selects production values |
| `k8s_client.py` | Kubernetes Python client wrapper (namespace, ResourceQuota, LimitRange, TLS, pods) |
| `helm_client.py` | Async subprocess wrapper around `helm` CLI (install, upgrade, uninstall, rollback) |
| `email_service.py` | SMTP email delivery for store credentials (Gmail App Password) |

### 3. Helm Charts

#### Platform Chart (`helm/platform/`)
Deploys the platform itself onto Kubernetes:
- **API Deployment** — FastAPI container with 12+ env vars (DB, JWT, OAuth, SMTP, CORS, etc.)
- **Dashboard Deployment** — React app served by nginx
- **Ingress** — routes `platform.local.store.dev` to the API/dashboard, supports TLS via cert-manager
- **Secrets** — `platform-secrets` K8s Secret for JWT key, Google OAuth secret, SMTP password
- **RBAC** — ServiceAccount + ClusterRole scoped to minimum required permissions
- **Values** — configurable replicas, images, resource limits, domain, auth, email

#### WooCommerce Chart (`helm/woocommerce/`)
Provisions a complete WordPress + WooCommerce store:
- **WordPress Deployment** — WordPress 6.4 with WooCommerce pre-installed
- **MySQL StatefulSet** — MySQL 8.0 with persistent storage (PVC)
- **WP-CLI Init Job** — Automated WordPress setup (install core, activate WooCommerce, create sample products)
- **Ingress** — per-store subdomain routing (`storename.local.store.dev`)
- **Secrets** — admin password, DB credentials (generated at runtime)
- **PVCs** — persistent storage for MySQL data and WordPress uploads
- Readiness/liveness probes on all containers

#### MedusaJS Chart (`helm/medusa/`)
Provisions a complete MedusaJS headless commerce stack:
- **Medusa Backend Deployment** — Node.js 18 running Medusa server on port 9000
- **PostgreSQL StatefulSet** — PostgreSQL 15 with persistent storage (PVC)
- **Redis Deployment** — Redis 7 for caching and session management
- **Storefront Deployment** — Next.js storefront on port 8000
- **Medusa Init Job** — Database migrations, seed data, admin user creation
- **Ingress** — per-store subdomain routing
- **Secrets** — admin password, DB credentials, JWT secret, cookie secret
- Readiness/liveness probes on all containers

### 4. Infrastructure Scripts (`scripts/`)

| Script | Purpose |
|--------|---------|
| `setup-local.sh` | Creates Kind cluster with ingress-ready node, installs NGINX Ingress Controller |
| `setup-prod.sh` | Installs k3s on VPS, configures kubeconfig, guides DNS/TLS setup |
| `teardown-local.sh` | Deletes the Kind cluster completely |
| `load-images-to-kind.sh` | Loads locally-built Docker images into the Kind cluster |
| `ingress-controller.yaml` | NGINX Ingress Controller manifests for Kind |

---

## Data Flow: Store Lifecycle

### Create Flow

```
User clicks "Create Store" in Dashboard
         │
         ▼
POST /api/v1/stores { name: "myshop", store_type: "woocommerce" }
         │  (Authorization: Bearer <JWT>)
         ▼
┌─────────────────────────────────────────────────────────────┐
│ routes.py :: create_store()                                  │
│  1. Authenticate user via JWT (401 if invalid)              │
│  2. Check per-user MAX_STORES_PER_USER (429 if exceeded)    │
│  3. Check name uniqueness (409 if duplicate — idempotent)   │
│  4. Check K8s namespace not Terminating (409 if so)         │
│  5. Generate namespace: "store-myshop"                      │
│  6. Insert Store record (status=PROVISIONING) into DB       │
│  7. Return 201 immediately (non-blocking)                   │
│  8. Enqueue background task → orchestrator.create_store()   │
└────────────────────────────┬────────────────────────────────┘
                             │ (background)
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ orchestrator.py :: _provision()                              │
│                                                              │
│  Step 1: Create Kubernetes namespace "store-myshop"         │
│          with labels (managed-by, store-name, store-type)   │
│          ↳ Idempotent: skips if namespace already exists    │
│                                                              │
│  Step 2: Apply ResourceQuota (CPU/memory/PVC caps)          │
│          Apply LimitRange (default container limits)        │
│          ↳ Idempotent: skips if already exists (409)        │
│                                                              │
│  Step 2.5: TLS handling                                     │
│          ↳ Local: copy self-signed cert to namespace        │
│          ↳ Production: skip (cert-manager handles TLS)      │
│                                                              │
│  Step 3: Helm install store chart                           │
│          ↳ Auto-selects values-prod.yaml when IN_CLUSTER    │
│          ↳ helm install myshop helm/woocommerce/            │
│             -f values-prod.yaml (if in-cluster)             │
│             --namespace store-myshop --wait                 │
│             --set wordpress.adminPassword=<generated>       │
│             --set mysql.rootPassword=<generated>            │
│             --set ingress.host=myshop.local.store.dev       │
│          ↳ Adds cert-manager annotation when in-cluster     │
│          ↳ Waits until all pods are Ready (or timeout)      │
│                                                              │
│  Step 4: Add /etc/hosts entry (local mode only)             │
│          127.0.0.1 myshop.local.store.dev                   │
│                                                              │
│  Step 5: Update DB → status=READY, store_url, admin_url    │
│          Store admin credentials in metadata_json           │
│          Send credentials email (if SMTP configured)        │
│                                                              │
│  On failure: status=FAILED, error_message saved to DB       │
└─────────────────────────────────────────────────────────────┘
```

### Delete Flow

```
User clicks "Delete" on store card
         │
         ▼
DELETE /api/v1/stores/{store_id}
         │  (Authorization: Bearer <JWT>)
         ▼
┌─────────────────────────────────────────────────────────────┐
│ routes.py :: delete_store()                                   │
│  1. Authenticate user via JWT (401 if invalid)               │
│  2. Verify store exists AND belongs to user (404 if not)     │
│  3. Check not already deleting (409 if so)                   │
│  4. Set status = DELETING                                    │
│  5. Return 200 immediately                                   │
│  6. Enqueue background task → orchestrator.delete_store()    │
└────────────────────────────┬────────────────────────────────┘
                             │ (background)
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ orchestrator.py :: delete_store()                             │
│                                                               │
│  Step 1: Helm uninstall (removes all chart-managed resources)│
│          ↳ Non-fatal warning if release not found            │
│                                                               │
│  Step 2: Delete Kubernetes namespace (Foreground propagation)│
│          ↳ Runs via asyncio.to_thread() (non-blocking)      │
│          ↳ K8s garbage-collects ALL resources in namespace   │
│          ↳ This is the safety net — nothing survives         │
│                                                               │
│  Step 2.5: Remove /etc/hosts entry (local mode only)         │
│                                                               │
│  Step 3: Delete Store record from database                   │
│          ↳ DB record removed only AFTER successful cleanup   │
│                                                               │
│  On failure: status=FAILED with error message                │
└─────────────────────────────────────────────────────────────┘
```

---

## Multi-Tenant Isolation Strategy

The platform enforces **namespace-per-store** isolation — every store runs in a dedicated Kubernetes namespace with hard resource boundaries.

### Isolation Layers

```
┌──────────────────────────────────────────────────────────┐
│  Layer 1: Namespace Isolation                            │
│  ↳ Each store = own namespace (store-{name})             │
│  ↳ All resources scoped to that namespace                │
│  ↳ Deleting namespace deletes everything (clean teardown)│
├──────────────────────────────────────────────────────────┤
│  Layer 2: Resource Quotas                                │
│  ↳ Per-namespace caps on CPU, memory, PVCs, storage      │
│  ↳ No single store can starve the cluster                │
├──────────────────────────────────────────────────────────┤
│  Layer 3: Limit Ranges                                   │
│  ↳ Default CPU/memory per container: 500m / 512Mi        │
│  ↳ Max per container: 2 cores / 4Gi                      │
│  ↳ Prevents runaway resource usage within a namespace    │
├──────────────────────────────────────────────────────────┤
│  Layer 4: Network Isolation                              │
│  ↳ Database services (MySQL, PostgreSQL, Redis) are      │
│    ClusterIP — unreachable from outside the cluster      │
│  ↳ Only Ingress exposes the storefront                   │
├──────────────────────────────────────────────────────────┤
│  Layer 5: RBAC                                           │
│  ↳ Platform ServiceAccount has a scoped ClusterRole      │
│  ↳ Only necessary verbs on specific resource types       │
│  ↳ No cluster-admin                                      │
└──────────────────────────────────────────────────────────┘
```

### Resource Quotas per Store Namespace

| Resource | Limit |
|----------|-------|
| Max pods | 20 |
| CPU requests (total) | 2 cores |
| Memory requests (total) | 4 GiB |
| CPU limits (total) | 4 cores |
| Memory limits (total) | 8 GiB |
| Persistent volume claims | 5 |
| Total storage | 20 GiB |

### Default Container Limits (LimitRange)

| Resource | Default Request | Default Limit | Max Allowed |
|----------|----------------|---------------|-------------|
| CPU | 100m | 500m | 2 cores |
| Memory | 128 MiB | 512 MiB | 4 GiB |

---

## Idempotency Strategy

Every operation in the provisioning pipeline is designed to be **safely retryable**:

| Operation | Idempotency Mechanism |
|-----------|----------------------|
| **Store creation (API)** | Name-uniqueness check → 409 Conflict if duplicate |
| **Namespace creation** | K8s API returns 409 AlreadyExists → logged and skipped |
| **ResourceQuota / LimitRange** | K8s API returns 409 if exists → logged and skipped |
| **Helm install** | Same release name + namespace = no-op (Helm is idempotent) |
| **Concurrent provisioning** | Per-store `asyncio.Lock` — second call skips if lock is held |
| **Store deletion (API)** | 409 if already in DELETING state |
| **Namespace deletion** | K8s API returns 404 if already gone → logged and skipped |
| **Helm uninstall** | Non-fatal if release doesn't exist |

### Concurrency Control

```python
# In-memory per-store lock prevents duplicate provisioning
_provisioning_locks: dict[str, asyncio.Lock] = {}

async def create_store(self, store: Store):
    lock = _provisioning_locks.setdefault(store.id, asyncio.Lock())
    if lock.locked():
        return  # Idempotent skip — already provisioning
    async with lock:
        await self._provision(store)
```

---

## Failure Handling Approach

### Provisioning Failures

```
┌──────────────────────────────────────────────────────┐
│                Failure Scenarios                      │
├──────────────────────┬───────────────────────────────┤
│ Failure Point        │ Recovery Strategy              │
├──────────────────────┼───────────────────────────────┤
│ Namespace creation   │ Rare — usually permissions.   │
│ fails                │ Store marked FAILED.           │
│                      │ User deletes + retries.        │
├──────────────────────┼───────────────────────────────┤
│ Helm install fails   │ Timeout or image pull error.  │
│                      │ Store marked FAILED with error │
│                      │ message from Helm.             │
│                      │ Delete cleans up partial       │
│                      │ resources via namespace delete.│
├──────────────────────┼───────────────────────────────┤
│ API process crashes  │ Store stays in PROVISIONING.   │
│ mid-provisioning     │ K8s resources may be partially │
│                      │ created. User deletes and      │
│                      │ retries — namespace delete is  │
│                      │ the cleanup safety net.        │
├──────────────────────┼───────────────────────────────┤
│ Pod crashes after    │ Kubernetes restarts the pod    │
│ store is READY       │ automatically (restartPolicy). │
│                      │ StatefulSets preserve data.    │
├──────────────────────┼───────────────────────────────┤
│ Delete fails         │ Store marked FAILED with       │
│ (Helm uninstall)     │ delete error. Namespace delete │
│                      │ is attempted regardless.       │
│                      │ DB record preserved for retry. │
└──────────────────────┴───────────────────────────────┘
```

### Key Principles

1. **Store status is the source of truth** — always updated in the DB before/after each major step
2. **Namespace deletion is the ultimate cleanup** — even if Helm uninstall fails, deleting the namespace removes everything
3. **Errors are surfaced** — error messages from Helm and K8s are stored in `store.error_message` and visible in the dashboard
4. **No silent failures** — all exceptions are caught, logged, and reflected in store status

---

## Security Considerations

### Authentication & Authorization

```
┌─────────────────────────────────────────────────────────────┐
│ Auth Flow                                                    │
│                                                              │
│  1. User clicks "Login with Google" → OAuth redirect        │
│     ↳ CSRF state stored in-memory with 10-min TTL           │
│     ↳ Capped at 1000 entries to prevent memory leaks        │
│                                                              │
│  2. Google callback → exchange code for token               │
│     ↳ Verify CSRF state (reject if expired or missing)      │
│     ↳ Fetch user info from Google                           │
│     ↳ Create or update User record in DB                    │
│                                                              │
│  3. Issue JWT access token (7-day expiry)                   │
│     ↳ Contains user_id, email, issued_at                    │
│     ↳ Signed with JWT_SECRET_KEY (HS256)                    │
│                                                              │
│  4. All API requests require Authorization: Bearer <JWT>    │
│     ↳ Stores are scoped to the authenticated user           │
│     ↳ Users can only see/delete their own stores            │
│                                                              │
│  Production guard: API crashes on startup if JWT_SECRET_KEY │
│  is still the insecure default when IN_CLUSTER=true         │
└─────────────────────────────────────────────────────────────┘
```

### CORS Policy

| Environment | `allow_origins` | `allow_credentials` |
|-------------|----------------|---------------------|
| Local dev | `["*"]` | `False` (spec requirement) |
| Production (default) | `[FRONTEND_URL]` | `True` |
| Production (explicit) | `CORS_ORIGINS` env var (comma-separated) | `True` |

> **Note:** The browser CORS spec forbids `allow_origins=["*"]` with `allow_credentials=True`. The platform dynamically sets `credentials=False` when using wildcard origins.

### Secret Management

```
┌─────────────────────────────────────────────────────────────┐
│ Secret Flow                                                  │
│                                                              │
│  1. Orchestrator generates passwords at runtime              │
│     ↳ secrets.choice() — cryptographically secure            │
│     ↳ 16-char alphanumeric + special chars                   │
│                                                              │
│  2. Passed to Helm via --set flags                           │
│     ↳ Never written to disk (no temp values.yaml)            │
│                                                              │
│  3. Helm creates K8s Secret resources                        │
│     ↳ Base64 encoded in etcd                                 │
│     ↳ Encrypted at rest if K8s encryption provider is set    │
│                                                              │
│  4. Admin credentials stored in store.metadata_json          │
│     ↳ Visible only via API (for dashboard display)           │
│     ↳ In production: use external secret manager (Vault)     │
└─────────────────────────────────────────────────────────────┘
```

### RBAC Policy (Least Privilege)

The platform's ServiceAccount uses a scoped **ClusterRole** with only the verbs and resources it needs:

| API Group | Resources | Allowed Verbs |
|-----------|-----------|--------------|
| `""` (core) | namespaces | get, list, create, delete |
| `""` (core) | pods, services, PVCs, secrets, configmaps | get, list, watch, create, delete |
| `""` (core) | resourcequotas, limitranges | get, list, create, delete |
| `apps` | deployments, statefulsets | get, list, watch, create, delete |
| `networking.k8s.io` | ingresses | get, list, create, delete |
| `batch` | jobs | get, list, create, delete |

**Not granted:** `cluster-admin`, `update`/`patch` on most resources, access to CRDs, access to other namespaces' secrets.

### Container Hardening

- All containers have **resource requests and limits** set
- Database services (MySQL, PostgreSQL, Redis) are **ClusterIP only** — never publicly exposed
- WordPress runs with `fsGroup: 33` (www-data user)
- MySQL runs with `fsGroup: 999` (mysql user)
- Init containers use minimal base images (`busybox`, `wordpress:cli`)
- TLS secrets are created per-namespace and not shared across stores

### Input Validation

- Store names: strict regex `^[a-z0-9][a-z0-9\-]*[a-z0-9]$` — prevents injection and ensures DNS-safe names
- Store type: enum-validated (`woocommerce` or `medusa` only)
- Max store limit enforced at API level before any K8s operations

---

## Local vs Production Differences

All environment differences are handled via **Helm values files** and **environment variables** — zero code changes required.

| Concern | Local (Kind) | Production (k3s VPS) |
|---------|-------------|---------------------|
| **Cluster** | Kind (Docker-in-Docker) | k3s (lightweight K8s) |
| **Ingress Controller** | NGINX (Kind-specific) | Traefik (k3s built-in) |
| **Ingress Class** | `nginx` | `traefik` |
| **Domain** | `local.store.dev` + `/etc/hosts` | Real domain with DNS A records |
| **TLS** | Self-signed cert copied to namespace | cert-manager + Let's Encrypt (auto via annotation) |
| **TLS in Ingress** | Manual `tls:` block in values | Auto-generated when `cert-manager.io/cluster-issuer` annotation present |
| **Storage Class** | `standard` (Kind default) | `local-path` (k3s default) |
| **Database (platform)** | SQLite (`aiosqlite`) | PostgreSQL (`asyncpg`) — swap via `DATABASE_URL` |
| **CORS** | `allow_origins=["*"]`, `credentials=False` | `allow_origins=[FRONTEND_URL]`, `credentials=True` |
| **Helm Values** | `values.yaml` (base defaults) | Auto-selects `values-prod.yaml` when `IN_CLUSTER=true` |
| **JWT Secret** | Default (dev-only) | Must be set — app **crashes on startup** if default is used |
| **Secrets** | Generated at runtime, stored in K8s | `platform-secrets` K8s Secret (JWT, OAuth, SMTP) |
| **Container Images** | Built locally, loaded into Kind | Container registry (Docker Hub, ECR, GHCR) |
| **API Replicas** | 1 | Multiple (stateless, behind LoadBalancer) |
| **Resource Limits** | Minimal (development) | Production limits in `values-prod.yaml` |
| **DNS Resolution** | Manual `/etc/hosts` or nip.io | Wildcard DNS (`*.yourdomain.com`) |

### How it works

The orchestrator auto-detects the environment via `IN_CLUSTER` and selects the right values file:

```bash
# Local deployment (orchestrator uses values.yaml automatically)
helm install myshop helm/woocommerce/ \
  --namespace store-myshop \
  --set wordpress.adminPassword=<generated> \
  --set mysql.rootPassword=<generated> \
  --set ingress.host=myshop.local.store.dev

# Production deployment (orchestrator uses values-prod.yaml automatically)
helm install myshop helm/woocommerce/ \
  -f helm/woocommerce/values-prod.yaml \
  --namespace store-myshop \
  --set baseDomain=yourdomain.com \
  --set wordpress.adminPassword=<generated> \
  --set mysql.rootPassword=<generated> \
  --set ingress.annotations.cert-manager\.io/cluster-issuer=letsencrypt-prod
```

The ingress templates auto-generate a `tls:` block when a `cert-manager.io/cluster-issuer` annotation is present but `ingress.tls` is empty — no need to hardcode TLS host/secret names in values files.

### Platform deployment

```bash
helm install platform helm/platform/ \
  --namespace store-platform --create-namespace \
  --set config.baseDomain=yourdomain.com \
  --set config.ingressClass=traefik \
  --set config.databaseUrl="postgresql+asyncpg://user:pass@host/db" \
  --set config.frontendUrl="https://platform.yourdomain.com" \
  --set secrets.jwtSecretKey="$(openssl rand -hex 32)" \
  --set ingress.className=traefik \
  --set ingress.host=platform.yourdomain.com
```

---

## Scaling Approach

### Horizontal Scaling Matrix

| Component | Stateless? | Scalable? | Strategy |
|-----------|-----------|-----------|----------|
| **Dashboard (React/nginx)** | ✅ Yes | ✅ Easy | Increase `replicas`, add HPA |
| **Platform API (FastAPI)** | ✅ Yes* | ✅ Easy | Increase `replicas`, add HPA |
| **Store WordPress** | Mostly | ⚠️ Limited | Single instance per store (shared filesystem needed for multi) |
| **Store MySQL** | ❌ No | ⚠️ Complex | Primary-replica with read replicas for HA |
| **Store Medusa** | ✅ Yes | ✅ Easy | Stateless Node.js — scale replicas freely |
| **Store PostgreSQL** | ❌ No | ⚠️ Complex | Use managed DB or Patroni for HA |
| **Store Redis** | Depends | ⚠️ Limited | Single instance sufficient; Sentinel for HA |

> \* API is stateless per-request. SQLite doesn't support concurrent writes — set `DATABASE_URL` to PostgreSQL (`postgresql+asyncpg://...`) for multi-replica. OAuth state is in-memory, so multi-replica requires Redis for shared state (future enhancement).

### Current Bottleneck & Future Path

```
Current:
  API (1 replica) → Background task → Helm install (sequential)

Future (high throughput):
  API (N replicas) → Task Queue (Redis/RabbitMQ) → Worker Pods (M replicas)
                                                    ↳ Helm install (parallel)
```

### HPA Configuration (planned)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: platform-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: platform-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

---

## Abuse Prevention

| Mechanism | Implementation | Location |
|-----------|---------------|----------|
| **Per-user store limit** | `MAX_STORES_PER_USER` env var (default: 5) | `routes.py` — checked before creation |
| **Name validation** | Regex: `^[a-z0-9][a-z0-9\-]*[a-z0-9]$` | `schemas.py` — Pydantic validator |
| **Duplicate prevention** | Unique constraint on `store.name` | `models.py` + `routes.py` (409 Conflict) |
| **Resource caps** | ResourceQuota per namespace | `k8s_client.py` — applied during provisioning |
| **Container limits** | LimitRange per namespace | `k8s_client.py` — default limits for all containers |
| **Provisioning timeout** | Helm `--wait --timeout 600s` | `orchestrator.py` — fails if pods don't become ready |
| **Audit logging** | Structured logging with timestamps | All modules — via Python `logging` |
| **Rate limiting** | `RATE_LIMIT_PER_MINUTE` config | `config.py` (ready for middleware integration) |

---

## Observability

### Current Capabilities

| Signal | Implementation |
|--------|---------------|
| **Store status** | Dashboard polls `/api/v1/stores` every 5 seconds — shows Provisioning / Ready / Failed |
| **Error details** | Error messages from Helm/K8s stored in `store.error_message`, visible in UI |
| **Pod inspection** | `/api/v1/stores/{id}/pods` — shows pod name, phase, readiness |
| **Health check** | `/api/v1/health` — reports K8s connectivity and API version |
| **Structured logs** | `%(asctime)s | %(levelname)s | %(name)s | %(message)s` format throughout |
| **Readiness probes** | All store containers have HTTP/exec readiness probes |
| **Liveness probes** | All store containers have HTTP/exec liveness probes |

### Production Enhancements (Planned)

```
┌──────────────────────────────────────────────────────────┐
│  Metrics: Prometheus + fastapi-instrumentator            │
│  ↳ Request latency, store creation duration, error rates │
├──────────────────────────────────────────────────────────┤
│  Dashboards: Grafana                                     │
│  ↳ Stores created/deleted over time                      │
│  ↳ Provisioning success/failure rates                    │
│  ↳ Resource utilization per namespace                    │
├──────────────────────────────────────────────────────────┤
│  Logs: Loki / EFK stack                                  │
│  ↳ Centralized log aggregation from all pods             │
│  ↳ Searchable store provisioning event timeline          │
├──────────────────────────────────────────────────────────┤
│  Alerting: Prometheus Alertmanager                       │
│  ↳ Store stuck in PROVISIONING > 10 min                  │
│  ↳ FAILED store count > threshold                        │
│  ↳ Cluster resource utilization > 80%                    │
└──────────────────────────────────────────────────────────┘
```

---

## Technology Choices & Tradeoffs

| Decision | Choice | Why | Alternative Considered |
|----------|--------|-----|----------------------|
| **Backend framework** | FastAPI | Async-native, automatic OpenAPI docs, Pydantic validation, `BackgroundTasks` for async provisioning | Django (heavier), Flask (no native async) |
| **Provisioning engine** | Helm CLI (subprocess) | Full Helm power (templating, hooks, rollback, history) without reimplementation | Kubernetes Python client only (no templating), Pulumi (overhead) |
| **K8s interaction** | Python kubernetes-client | Direct API for namespace/quota ops that don't need Helm templating | Helm only (overkill for simple CRUD), kubectl subprocess (fragile) |
| **Metadata DB** | SQLite (aiosqlite) / PostgreSQL (asyncpg) | SQLite for local dev (zero-dependency), PostgreSQL for production (swap via `DATABASE_URL`) | MySQL (no native async), MongoDB (overkill) |
| **Frontend** | React + Vite | Fast HMR, modern ecosystem, lightweight | Next.js (SSR overkill for SPA), Vue (less ecosystem) |
| **Store isolation** | Namespace-per-store | Simple, native K8s, garbage-collection on delete | vCluster (complex), separate clusters (expensive) |
| **Ingress** | NGINX (local) / Traefik (prod) | NGINX for Kind compatibility, Traefik for k3s built-in | Ambassador, Istio (too complex for this use case) |
| **WooCommerce stack** | WordPress + MySQL | Official, stable, widely tested | Containerized Shopify (not possible), custom e-commerce (scope) |
| **MedusaJS stack** | Medusa + PostgreSQL + Redis | Modern headless commerce, Node.js, extensible | Saleor (Python, heavier), Vendure (less mature) |

---

## Upgrade & Rollback

### Helm Release Lifecycle

```bash
# View release history
helm history myshop --namespace store-myshop

# Upgrade chart (e.g., new WordPress version)
helm upgrade myshop helm/woocommerce/ \
  --namespace store-myshop \
  --set wordpress.image=wordpress:6.5-apache \
  --reuse-values

# Rollback to previous release
helm rollback myshop --namespace store-myshop

# Rollback to specific revision
helm rollback myshop 2 --namespace store-myshop
```

### Zero-Downtime Strategy

- WordPress deployments use `RollingUpdate` strategy (default)
- MySQL StatefulSet updates use `OnDelete` strategy for safety
- Helm `--wait` ensures new pods are Ready before marking upgrade complete
- Readiness probes prevent traffic routing to unready pods
- Rollback is always one command away (`helm rollback`)

---

*Last updated: February 2026*
