# System Design & Tradeoffs

## Architecture Choice

**Pattern: API-driven orchestrator + Helm-based provisioning**

The platform follows a simple but production-viable architecture:

```
User → React Dashboard → FastAPI API → Kubernetes (via Helm CLI + K8s API)
```

### Why this design?

1. **FastAPI** handles HTTP requests and kicks off provisioning as **background tasks** — the API responds immediately ("provisioning") while the actual Helm install runs async.

2. **Helm CLI** (shelled out via `asyncio.create_subprocess_exec`) is the provisioning engine — this gives us the full power of Helm (templating, hooks, rollback, history) without reimplementing it.

3. **Kubernetes Python client** handles namespace CRUD, ResourceQuota/LimitRange creation, and pod inspection — things that are simpler via the K8s API than Helm.

4. **SQLite** (async via aiosqlite) as the store metadata database — simple, zero-dependency, sufficient for this scale. In production, swap to PostgreSQL via `DATABASE_URL` env var.

---

## Multi-Store Isolation

**Namespace-per-store** is the primary isolation boundary:

- Each store gets its own namespace (`store-{name}`)
- **ResourceQuota** per namespace: caps CPU, memory, PVCs, pod count
- **LimitRange** per namespace: sets default container limits so no pod can run unbounded
- Deleting a store = deleting the namespace (Kubernetes garbage-collects everything inside)

### Resource Guardrails (per store namespace)

| Resource | Limit |
|----------|-------|
| Pods | 20 |
| CPU requests | 2 cores |
| Memory requests | 4Gi |
| CPU limits | 4 cores |
| Memory limits | 8Gi |
| PVCs | 5 |
| Storage | 20Gi |

---

## Idempotency & Failure Handling

### Idempotent creation
- **DB check**: Before creating, we check if a store with the same name exists (409 Conflict)
- **Namespace creation**: Uses K8s API — if namespace exists, we skip (no error)
- **Helm install**: Helm itself is idempotent for a given release name in a namespace
- **In-memory lock**: A per-store `asyncio.Lock` prevents duplicate concurrent provisioning of the same store

### Failure recovery
- If provisioning fails at any step, the store status is set to `FAILED` with the error message
- The user can delete the failed store (cleans up any partial resources) and retry
- If the API process restarts mid-provisioning, the store stays in "provisioning" status — the user can delete and recreate

### Cleanup guarantees
- **Helm uninstall** removes all chart-managed resources
- **Namespace deletion** (with `Foreground` propagation) is the final safety net — K8s deletes everything in the namespace
- The DB record is removed only after successful cleanup

---

## Security Posture

### Secrets
- **No hardcoded secrets in source code** — passwords are generated at runtime using `secrets.choice()`
- Secrets are passed to Helm via `--set` flags (never written to files on disk)
- In K8s, secrets are stored as `kind: Secret` resources (base64 encoded, encrypted at rest if K8s is configured for it)

### RBAC
- The platform ServiceAccount has a **ClusterRole** scoped to only the resources it needs:
  - Namespaces: create/delete
  - Pods, Services, PVCs, Secrets: CRUD within store namespaces
  - ResourceQuotas, LimitRanges: create
  - Deployments, StatefulSets, Ingress, Jobs: CRUD
- No cluster-admin privileges

### Container hardening
- WordPress runs with `fsGroup: 33` (www-data)
- MySQL runs with `fsGroup: 999` (mysql)
- Init containers use minimal `busybox` image
- Resource limits on all containers

### Network exposure
- Only **Ingress** resources are publicly routable
- MySQL, PostgreSQL, Redis services are `ClusterIP` (internal only)
- Platform API is `ClusterIP` when deployed on K8s (exposed via Ingress)

---

## What Changes for Production

| Concern | Local (Kind) | Production (k3s VPS) |
|---------|-------------|---------------------|
| Ingress controller | nginx (Kind-specific manifest) | Traefik (k3s built-in) |
| Ingress class | `nginx` | `traefik` |
| Domain | `local.store.dev` + /etc/hosts | Real domain with DNS A records |
| TLS | None | cert-manager + Let's Encrypt |
| Storage class | `standard` (Kind default) | `local-path` (k3s default) |
| Database | SQLite | PostgreSQL (change `DATABASE_URL`) |
| Secrets | Generated at runtime | External secret manager (Vault, AWS SM) |
| Container images | Local build | Container registry (Docker Hub, ECR) |
| Replicas | 1 | Multiple (API is stateless, scales horizontally) |
| Resources | Minimal | Production limits in `values-prod.yaml` |

All differences are handled via Helm values files (`values-local.yaml` vs `values-prod.yaml`).

---

## Horizontal Scaling Plan

### What scales horizontally
- **Dashboard** — stateless React SPA served by nginx (scale replicas freely)
- **API** — FastAPI is stateless per-request; multiple replicas behind a Service
- **Provisioning throughput** — currently runs in API's background tasks; for higher throughput, extract to a task queue (Celery/Redis) with dedicated worker pods

### Stateful constraints
- **SQLite** doesn't support concurrent writes from multiple processes — replace with PostgreSQL for multi-replica API
- **Helm CLI** is stateless (release info stored in K8s secrets) — safe to run concurrently
- **Store databases** (MySQL/PostgreSQL per store) are inherently single-instance; for HA, use managed databases or primary-replica setups

---

## Abuse Prevention

1. **Max stores limit** — configurable via `MAX_STORES` env var (default: 10)
2. **Store name validation** — strict regex (`^[a-z0-9][a-z0-9-]*[a-z0-9]$`) prevents injection
3. **ResourceQuota per namespace** — prevents any single store from consuming excessive cluster resources
4. **Provisioning timeout** — Helm install has a configurable timeout (default: 300s)
5. **Duplicate prevention** — unique constraint on store name, idempotent namespace creation
6. **Audit trail** — all actions logged with timestamps (structured logging in the API)

---

## Observability

- **Store status** surfaced in the dashboard (Provisioning / Ready / Failed with error details)
- **Pod status** available via `/api/v1/stores/{id}/pods` endpoint
- **Structured logging** throughout the backend (`logging` module with timestamps + level + component)
- **Health endpoint** (`/api/v1/health`) checks K8s connectivity

For production, add:
- Prometheus metrics (fastapi-instrumentator)
- Grafana dashboards for store creation/failure rates
- Loki for centralized log aggregation
