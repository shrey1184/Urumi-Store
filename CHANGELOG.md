# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Comprehensive test coverage
- MedusaJS store type completion
- Prometheus metrics export
- Store backup/restore functionality
- Multi-cluster support

## [1.0.0] - 2026-02-12

### Added
- Initial release
- WooCommerce store provisioning
- React dashboard with real-time status updates
- FastAPI backend with async orchestration
- Kubernetes integration via Python client
- Helm chart management
- Multi-tenant namespace isolation with resource quotas
- Background provisioning with status tracking
- Pod inspection API
- Health check endpoints
- Local Kind cluster setup scripts
- Production k3s setup scripts
- NGINX Ingress integration
- Store creation, listing, and deletion
- Auto-generated admin credentials
- WP-CLI setup job for WooCommerce initialization
- Comprehensive documentation

### Technical Details
- FastAPI 0.109.0
- React 18.2.0 + Vite
- Kubernetes Python Client 28.1.0
- Helm 3 integration
- SQLite with async support (aiosqlite)
- Resource quotas per namespace (2 CPU, 4Gi memory)

### Known Limitations
- SQLite not suitable for high concurrency
- No TLS in local setup
- Manual DNS configuration required
- Single cluster support only

---

## Version History

- **1.0.0** - Initial public release

[Unreleased]: https://github.com/yourusername/Urumi-Ai/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/yourusername/Urumi-Ai/releases/tag/v1.0.0
