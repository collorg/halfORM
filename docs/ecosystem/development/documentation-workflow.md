# Documentation Workflow Guide

This guide explains how halfORM's documentation is managed with multi-version support, automated deployment, and structured release process.

## Overview

halfORM uses a GitFlow-inspired workflow with automated documentation deployment for different stages of development:

- **Development versions** (`dev/*`) - Work in progress, patches preparation
- **Release candidates** (`release/*`) - Pre-release testing
- **Stable releases** (tags `v*`) - Production-ready versions
- **Main development** (`main`) - Latest development state

## Branch Structure

```
main                    # Latest stable development
├── dev/0.16.x         # Patches in preparation for 0.16.x
├── release/0.16.x     # Release candidate for 0.16.x
├── feature/new-cli    # Feature development
└── hotfix/urgent-fix  # Urgent fixes
```

## Documentation Deployment

### Automatic Deployment

The documentation is automatically built and deployed via GitHub Actions when pushing to specific branches or creating tags:

| Branch/Tag Pattern | Version Deployed | URL | Description |
|-------------------|------------------|-----|-------------|
| `main` | `dev` | `/dev/` | Latest development documentation |
| `dev/X.Y.x` | `X.Y.x-dev` | `/X.Y.x-dev/` | Patch development for version X.Y |
| `release/X.Y.x` | `X.Y.x-rc` | `/X.Y.x-rc/` | Release candidate documentation |
| `vX.Y.Z` (tags) | `X.Y.Z` | `/X.Y.Z/` + `/latest/` | Stable release (becomes default) |

### URL Structure

```
https://collorg.github.io/halfORM/
├── /                   # → Redirects to latest stable
├── /latest/           # → Current stable version (alias)
├── /0.16.0/          # → Specific stable version
├── /0.16.x-rc/       # → Release candidate
├── /0.16.x-dev/      # → Development patches
└── /dev/             # → Main branch development
```

## Development Workflow

### 1. Feature Development

```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/new-feature

# Work on feature + documentation
# ... make changes ...

# Push and create PR
git push origin feature/new-feature
# → No documentation deployment (feature branches ignored)
```

### 2. Patch Development

```bash
# Create or switch to dev branch
git checkout -b dev/0.16.x  # or git checkout dev/0.16.x
git pull origin dev/0.16.x

# Work on patches + documentation updates
# ... make changes ...

# Push changes
git push origin dev/0.16.x
# → Automatically deploys to /0.16.x-dev/
```

### 3. Release Preparation

```bash
# Create release branch
git checkout -b release/0.16.x
git merge dev/0.16.x  # Include patches

# Final testing and documentation polish
# ... make final changes ...

# Push release candidate
git push origin release/0.16.x
# → Automatically deploys to /0.16.x-rc/
```

### 4. Stable Release

```bash
# Create release tag
git tag v0.16.0 -m "release: halfORM 0.16.0 with unified CLI"
git push origin v0.16.0
# → Automatically deploys to /0.16.0/ and /latest/
# → Sets /latest/ as default version
```

### 5. Hotfix Process

```bash
# Create hotfix from main
git checkout main
git checkout -b hotfix/urgent-fix

# Fix + documentation
# ... make changes ...

# Push to main and create patch release
git checkout main
git merge hotfix/urgent-fix
git push origin main
# → Deploys to /dev/

# Create patch release
git tag v0.16.1 -m "hotfix: urgent fix"
git push origin v0.16.1
# → Deploys to /0.16.1/ and updates /latest/
```

## Local Development

### Prerequisites

```bash
# Install dependencies
pip install mkdocs-material mkdocstrings-python mkdocs-git-revision-date-localized-plugin mike
```

### Local Testing

```bash
# Serve current documentation (single version)
mkdocs serve

# Deploy version locally for testing
./scripts/deploy-docs.sh deploy dev
./scripts/deploy-docs.sh deploy 0.16.0-rc latest

# Serve multi-version documentation
./scripts/deploy-docs.sh serve
```

### Local Version Management

```bash
# List deployed versions
./scripts/deploy-docs.sh list

# Deploy specific version
./scripts/deploy-docs.sh deploy 0.16.0 latest

# Set default version
./scripts/deploy-docs.sh set-default latest

# Delete version
./scripts/deploy-docs.sh delete 0.16.0-rc1

# Build documentation
./scripts/deploy-docs.sh build
```

## Content Management

### Version-Specific Content

Use conditional blocks for version-specific content:

```markdown
{% if version == "0.16.0" %}
This feature is new in version 0.16.0.
{% endif %}

{% if version != "dev" %}
This applies to stable versions only.
{% endif %}
```

### Migration Information

When creating a new major version:

1. **Update version references** in `docs/index.md`
2. **Add migration guide** if breaking changes exist
3. **Update CLI examples** to reflect new commands
4. **Add new features** to relevant sections
5. **Test all version links** and cross-references

### Cross-Version Compatibility

- Keep URLs stable across versions when possible
- Use relative links for internal references
- Document breaking changes prominently
- Provide clear migration paths

## GitHub Actions Configuration

The documentation workflow is configured in `.github/workflows/docs.yml`:

```yaml
name: Documentation
on:
  push:
    branches: [ main, 'release/*', 'dev/*' ]
    tags: [ 'v*' ]
  pull_request:
    branches: [ main ]
```

### Permissions Required

```yaml
permissions:
  contents: write
  pages: write
  id-token: write
```

## Manual Deployment

### Emergency Deployment

If automatic deployment fails:

```bash
# Local emergency deployment
git checkout main
mike deploy --push dev
mike set-default --push dev

# Or for stable version
mike deploy --push --update-aliases 0.16.0 latest
mike set-default --push latest
```

### Cleanup Operations

```bash
# Remove old versions
mike delete --push 0.15.0 0.14.0

# Complete reset (use with caution)
mike delete --all --push
```

## Best Practices

### Documentation Updates

1. **Always update documentation** with code changes
2. **Test locally** before pushing
3. **Use meaningful commit messages** for documentation changes
4. **Include migration notes** for breaking changes

### Version Management

1. **Keep stable versions** for reference
2. **Clean up old development versions** regularly
3. **Document version lifecycle** in release notes
4. **Test all deployed versions** after releases

### Content Guidelines

1. **Use consistent formatting** across versions
2. **Include version compatibility** information
3. **Provide working examples** for each version
4. **Maintain backward compatibility** in URLs when possible

## Troubleshooting

### Common Issues

**Documentation not updating:**
- Check GitHub Actions logs
- Verify branch/tag naming conventions
- Ensure GitHub Pages is enabled

**Version conflicts:**
```bash
# Reset local gh-pages branch
git fetch origin
git checkout gh-pages
git reset --hard origin/gh-pages
```

**Local mike issues:**
```bash
# Clean mike cache
rm -rf .git/refs/heads/gh-pages
git branch -D gh-pages
```

### Getting Help

- Check GitHub Actions logs for deployment issues
- Review mike documentation for advanced usage
- Test locally before pushing to production
- Use issue templates for bug reports

## Examples

### Complete Release Cycle

```bash
# 1. Development phase
git checkout -b dev/0.16.x
# ... work on features ...
git push origin dev/0.16.x  # → /0.16.x-dev/

# 2. Release preparation
git checkout -b release/0.16.x
git merge dev/0.16.x
# ... final polish ...
git push origin release/0.16.x  # → /0.16.x-rc/

# 3. Release
git tag v0.16.0
git push origin v0.16.0  # → /0.16.0/ + /latest/

# 4. Hotfix
git checkout main
git checkout -b hotfix/critical-fix
# ... fix issue ...
git checkout main
git merge hotfix/critical-fix
git tag v0.16.1
git push origin v0.16.1  # → /0.16.1/ + /latest/
```

### Version Cleanup

```bash
# Remove old development versions
mike delete --push 0.15.x-dev 0.14.x-dev

# Keep last 3 stable versions
mike list
mike delete --push 0.13.0 0.12.0  # Remove older versions
```

This workflow ensures consistent, automated documentation deployment while maintaining flexibility for different development stages and easy rollback capabilities.
