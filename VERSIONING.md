# Version Management Guide

## Versioning Strategy

This project follows [Semantic Versioning](https://semver.org/) (SemVer) with the format `MAJOR.MINOR.PATCH`:

- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions
- **PATCH** version for backwards-compatible bug fixes

## Current Versions

| Version | Tag | Description | Date |
|---------|-----|-------------|------|
| v1.5.3 | `v1.5.3` | FastMCP Streamable HTTP transport for Kubernetes compatibility | Current |
| v1.5.2 | `v1.5.2` | Health check endpoint, development workflow fixes | Previous |
| v1.5.0 | `v1.5.0` | HTTP transport support, enhanced tool coverage | Previous |
| v1.1.0 | `v1.1.0` | Kubernetes deployment fixes, troubleshooting guide | Previous |
| v1.0.0 | `v1.0.0` | Initial release | Previous |

## Available Docker Images

### Production Images (Recommended)
```bash
# Latest stable release
docker pull ghcr.io/ekenheim/mcp-polygon:v1.5.3

# Previous stable release
docker pull ghcr.io/ekenheim/mcp-polygon:v1.5.2
```

### Development Images
```bash
# Latest from main branch
docker pull ghcr.io/ekenheim/mcp-polygon:main

# Latest commit SHA
docker pull ghcr.io/ekenheim/mcp-polygon:sha-<commit-hash>
```

## Release Process

### 1. Create a New Release

```bash
# 1. Update version in code if needed
# 2. Commit your changes
git add .
git commit -m "Prepare for v1.2.0 release"

# 3. Create and push a new tag
git tag -a v1.5.3 -m "Release v1.5.3: FastMCP Streamable HTTP transport for Kubernetes compatibility"
git push origin v1.5.3
```

### 2. GitHub Actions Automatically Builds

When you push a tag, GitHub Actions will:
- Build the Docker image
- Tag it with the version number
- Push to GitHub Container Registry
- Create a GitHub release

### 3. Update Your Deployments

Update your HelmRelease or Kubernetes deployment:

```yaml
# For Helm
image:
  repository: ghcr.io/ekenheim/mcp-polygon
  tag: v1.5.3  # Update to new version

# For Kubernetes
image: ghcr.io/ekenheim/mcp-polygon:v1.5.3
```

## Version Update Checklist

### Before Creating a New Version

- [ ] All tests pass
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated (if you have one)
- [ ] Version numbers in code are updated (if applicable)
- [ ] Docker image builds successfully

### After Creating a New Version

- [ ] Verify the Docker image is available: `docker pull ghcr.io/ekenheim/mcp-polygon:v1.5.3`
- [ ] Test the new image locally
- [ ] Update your production deployments
- [ ] Monitor the deployment for any issues
- [ ] Update this VERSIONING.md file

## Rollback Strategy

If you need to rollback to a previous version:

```bash
# 1. Identify the previous working version
# 2. Update your deployment to use the previous version
# 3. Redeploy

# Example: Rollback to v1.0.0
kubectl set image deployment/mcp-polygon mcp-server=ghcr.io/ekenheim/mcp-polygon:v1.0.0
```

## Best Practices

### For Production
- ✅ Use specific version tags (e.g., `v1.5.3`)
- ✅ Test new versions in staging first
- ✅ Keep previous version available for rollback
- ❌ Avoid using `latest` or `main` tags

### For Development
- ✅ Use `main` tag for latest development builds
- ✅ Use commit SHA tags for debugging specific issues
- ✅ Test with versioned tags before production

## Version Compatibility

| MCP Server Version | Polygon.io API | Python Version | Notes |
|-------------------|----------------|----------------|-------|
| v1.5.5 | v2/v3 | 3.9+ | Current stable - SSE transport for Langflow |
| v1.5.3 | v2/v3 | 3.9+ | Previous stable |
| v1.5.2 | v2/v3 | 3.9+ | Previous stable |
| v1.5.0 | v2/v3 | 3.9+ | Previous stable |
| v1.0.0 | v2/v3 | 3.9+ | Initial release |

## Support Matrix

- **v1.5.3**: Full support, recommended for production
- **v1.0.0**: Security updates only
- **main**: Development, no guarantees
