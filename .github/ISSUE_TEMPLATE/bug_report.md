---
name: Bug report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description
A clear and concise description of what the bug is.

## To Reproduce
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

## Expected Behavior
A clear and concise description of what you expected to happen.

## Actual Behavior
What actually happened.

## Environment
- **OS**: [e.g., Ubuntu 22.04, macOS 14]
- **Kubernetes**: [e.g., Kind 0.20.0, k3s v1.28]
- **Python version**: [e.g., 3.11.5]
- **Node.js version**: [e.g., 18.17.0]
- **Helm version**: [e.g., 3.14.0]
- **Browser** (if frontend issue): [e.g., Chrome 120, Firefox 121]

## Logs/Screenshots
If applicable, add logs or screenshots to help explain your problem.

### Backend Logs
```
Paste relevant backend logs here
```

### Frontend Logs
```
Paste browser console errors here
```

### Kubernetes Logs
```bash
kubectl get pods -n store-<name>
kubectl logs -n store-<name> <pod-name>
```

## Additional Context
Add any other context about the problem here.
