# Contributing to Urumi-Ai

Thank you for your interest in contributing to Urumi-Ai! 🎉

## Development Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/<your-username>/Urumi-Ai.git`
3. Create a feature branch: `git checkout -b feature/amazing-feature`
4. Follow the setup instructions in [README.md](README.md)

## Code Standards

### Backend (Python)
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Add docstrings for public functions
- Run linting: `ruff check .` (install with `pip install ruff`)
- Format code: `black .` (install with `pip install black`)

### Frontend (JavaScript/React)
- Follow ESLint configuration in `Frontend/eslint.config.js`
- Use functional components with hooks
- Format with Prettier: `npm run format` (if configured)

### Helm Charts
- Follow Helm best practices
- Test charts with `helm lint`
- Document all values in `values.yaml`

## Testing

### Backend
```bash
cd Backend
pytest tests/  # (when tests are added)
```

### Frontend
```bash
cd Frontend
npm test  # (when tests are added)
```

### Integration Testing
```bash
# Test full store lifecycle
./scripts/setup-local.sh
# Create store via UI
# Verify store is accessible
# Delete store
# Verify cleanup
```

## Pull Request Process

1. Update the README.md with details of changes if needed
2. Update the SYSTEM_DESIGN.md if architecture changes
3. Ensure all tests pass
4. Update version numbers if applicable
5. Create a descriptive PR with:
   - What changed
   - Why it changed
   - How to test it

## Commit Message Guidelines

Follow conventional commits:
- `feat:` new feature
- `fix:` bug fix
- `docs:` documentation only
- `style:` formatting, missing semicolons, etc.
- `refactor:` code restructuring
- `test:` adding tests
- `chore:` maintenance tasks

Example: `feat: add support for Shopify store type`

## Areas for Contribution

### High Priority
- [ ] Add comprehensive unit tests
- [ ] Implement store update/upgrade functionality
- [ ] Add Prometheus metrics export
- [ ] Support custom Helm values per store
- [ ] Add store backup/restore functionality

### Medium Priority
- [ ] Implement store cloning
- [ ] Add resource usage monitoring dashboard
- [ ] Support multiple K8s clusters
- [ ] Add webhook notifications (Slack, Discord)

### Nice to Have
- [ ] Add CI/CD pipeline (GitHub Actions)
- [ ] Create video tutorials
- [ ] Add more ecommerce platforms (Shopify, other engines)
- [ ] Implement A/B testing for stores
- [ ] Add cost estimation per store

## Questions?

Open an issue with the `question` label or reach out to the maintainers.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Assume good intentions

---

Happy coding! 🚀
