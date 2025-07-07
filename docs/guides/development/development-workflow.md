# Development Workflow Guide

This guide explains halfORM's development workflow, from feature development to stable releases, including code management, testing, and PyPI publishing.

## Overview

halfORM follows a GitFlow-inspired workflow with automated CI/CD, comprehensive testing, and coordinated documentation deployment. The workflow supports multiple concurrent development streams while maintaining stability.

## Branch Structure

```
main                    # Latest stable development
├── dev/0.16.x         # Patches in preparation for 0.16.x
├── release/0.16.x     # Release candidate for 0.16.x
├── maint/0.15.x       # Maintenance branch for 0.15.x series
├── feature/new-cli    # Feature development
├── hotfix/urgent-fix  # Urgent fixes
└── docs/update-guide  # Documentation-only changes
```

## Development Phases

### 1. Feature Development

**Purpose**: Develop new features or significant improvements

```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/unified-cli

# Development cycle
# ... implement feature ...
# ... write tests ...
# ... update documentation ...

# Push and create PR
git push origin feature/unified-cli
# Create Pull Request to main
```

**Checklist**:

- [ ] Code implements feature specification
- [ ] All tests pass (`pytest`)
- [ ] Documentation updated
- [ ] CLI changes reflected in help text
- [ ] Breaking changes documented

### 2. Patch Development

**Purpose**: Bug fixes, minor improvements, and maintenance

```bash
# Create or checkout dev branch
git checkout -b dev/0.16.x  # or git checkout dev/0.16.x
git pull origin dev/0.16.x

# Development cycle
# ... fix bugs ...
# ... add tests ...
# ... update docs ...

# Push changes
git push origin dev/0.16.x
```

**Checklist**:

- [ ] Bug fixes include regression tests
- [ ] Backward compatibility maintained
- [ ] Version number updated if needed
- [ ] Changelog updated

### 3. Release Preparation

**Purpose**: Prepare stable release with thorough testing

```bash
# Create release branch
git checkout -b release/0.16.x
git merge dev/0.16.x  # Include all patches

# Release preparation
# ... final testing ...
# ... version number finalization ...
# ... changelog completion ...

# Push release candidate
git push origin release/0.16.x
```

**Checklist**:

- [ ] All tests pass on multiple Python versions
- [ ] Documentation is complete and accurate
- [ ] Version number is correct in `half_orm/version.txt`
- [ ] Changelog is updated
- [ ] PyPI package builds successfully
- [ ] CLI help text is accurate

### 4. Stable Release

**Purpose**: Create production-ready release

```bash
# Final release preparation
git checkout release/0.16.x
# ... final commits if needed ...

# Create release tag
git tag v0.16.0 -m "release: halfORM 0.16.0 with unified CLI"
git push origin v0.16.0

# Merge back to main
git checkout main
git merge release/0.16.x
git push origin main
```

**Checklist**:

- [ ] Tag follows semantic versioning (`vX.Y.Z`)
- [ ] GitHub release created with release notes
- [ ] PyPI package published
- [ ] Documentation deployed
- [ ] Release announcement prepared

### 5. Hotfix Process

**Purpose**: Emergency fixes for production issues

```bash
# Create hotfix from the affected production version
git checkout v0.16.0  # Latest production tag
git checkout -b hotfix/critical-security-fix

# Quick fix
# ... minimal changes ...
# ... targeted tests ...

# Apply fix to production branch first
git checkout release/0.16.x  # or create if doesn't exist
git cherry-pick hotfix/critical-security-fix

# Create emergency patch release
git tag v0.16.1 -m "hotfix: critical security fix"
git push origin v0.16.1

# Apply fix to development branches
git checkout dev/0.16.x
git cherry-pick hotfix/critical-security-fix
git push origin dev/0.16.x

# Apply fix to main
git checkout main
git cherry-pick hotfix/critical-security-fix
git push origin main

# Clean up hotfix branch
git branch -d hotfix/critical-security-fix
```

**Multi-version hotfix** (if multiple versions affected):
```bash
# Fix affects 0.15.x and 0.16.x
git checkout hotfix/critical-security-fix

# Apply to 0.15.x maintenance branch
git checkout maint/0.15.x  # or create from v0.15.latest
git cherry-pick hotfix/critical-security-fix
git tag v0.15.4 -m "hotfix: critical security fix"
git push origin v0.15.4

# Apply to 0.16.x production branch
git checkout release/0.16.x
git cherry-pick hotfix/critical-security-fix
git tag v0.16.1 -m "hotfix: critical security fix"
git push origin v0.16.1

# Apply to development branches
git checkout dev/0.16.x
git cherry-pick hotfix/critical-security-fix
git push origin dev/0.16.x

git checkout main
git cherry-pick hotfix/critical-security-fix
git push origin main
```

**Checklist**:

- [ ] Minimal, targeted changes only
- [ ] Security fixes tested thoroughly
- [ ] Patch version incremented on all affected branches
- [ ] Emergency release notes prepared
- [ ] Fix applied to all production versions (cherry-pick)
- [ ] Fix applied to all development branches
- [ ] All affected versions tagged and released
- [ ] Documentation updated if user-facing changes

## Version Management

### Semantic Versioning

halfORM follows [Semantic Versioning](https://semver.org/):

- **Major** (`1.0.0` → `2.0.0`): Breaking changes
- **Minor** (`0.15.0` → `0.16.0`): New features, backward compatible
- **Patch** (`0.16.0` → `0.16.1`): Bug fixes, backward compatible

### Version Files

```bash
# Update version in
half_orm/version.txt          # Main version file
setup.py                      # Package metadata
docs/index.md                 # Documentation version
```

### Pre-release Versions

```bash
# Development versions
0.16.0-dev       # Development branch
0.16.0-rc1       # Release candidate
0.16.0-alpha1    # Alpha release
0.16.0-beta1     # Beta release
```

## Testing Strategy

### Test Levels

1. **Unit Tests**: Individual functions and classes
2. **Integration Tests**: Database interactions
3. **CLI Tests**: Command-line interface
4. **Documentation Tests**: Code examples in docs

### Test Execution

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/              # Unit tests
pytest tests/integration/       # Integration tests
pytest tests/cli/              # CLI tests

# Run with coverage
pytest --cov=half_orm --cov-report=html

# Test multiple Python versions
tox
```

### Continuous Integration

GitHub Actions runs tests on:
- **Python versions**: 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13
- **PostgreSQL versions**: 9.6, 10, 11, 12, 13, 14, 15, 16, 17
- **Operating systems**: Ubuntu, macOS, Windows

## Release Process

### 1. Pre-release Checklist

- [ ] All tests pass on CI
- [ ] Documentation is complete
- [ ] Version numbers updated
- [ ] Changelog prepared
- [ ] Migration guide written (if needed)

### 2. Release Preparation

```bash
# Update version
echo "0.16.0" > half_orm/version.txt

# Update documentation
# Edit docs/index.md to reflect new version

# Update changelog
# Edit CHANGELOG.md

# Commit changes
git add .
git commit -m "chore: prepare release 0.16.0"
```

### 3. Release Creation

```bash
# Create annotated tag
git tag -a v0.16.0 -m "release: halfORM 0.16.0

Major improvements:
- Unified CLI interface
- Automatic extension discovery
- Enhanced database inspection
- Improved developer experience

Breaking changes:
- Development tools moved to half-orm-dev package
- CLI commands restructured under unified interface

Migration guide: https://collorg.github.io/halfORM/guides/migration/"

# Push tag
git push origin v0.16.0
```

### 4. PyPI Publishing

```bash
# Build package
python -m build

# Upload to PyPI (automated via GitHub Actions)
# Manual upload if needed:
# python -m twine upload dist/*
```

### 5. Post-release

```bash
# Create GitHub release
# - Go to GitHub releases
# - Create release from tag
# - Add release notes
# - Upload additional files if needed

# Update development version
echo "0.17.0-dev" > half_orm/version.txt
git add half_orm/version.txt
git commit -m "chore: bump version to 0.17.0-dev"
git push origin main
```

## Code Quality

### Code Style

```bash
# Format code
black half_orm/
black tests/

# Lint code
pylint half_orm/
flake8 half_orm/

# Type checking
mypy half_orm/
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

### Code Review

**All changes require**:

- [ ] Code review by at least one maintainer
- [ ] All CI checks passing
- [ ] Documentation updated
- [ ] Tests added/updated

## Extension Development

### Creating Extensions

```bash
# Extension structure
half-orm-extension/
├── half_orm_extension/
│   ├── __init__.py
│   ├── cli_extension.py     # CLI integration
│   └── core.py             # Main functionality
├── tests/
├── docs/
└── setup.py
```

### Extension Integration

```python
# half_orm_extension/cli_extension.py
import click

EXTENSION_INFO = {
    'description': 'Extension for X functionality',
    'commands': ['generate', 'serve', 'deploy']
}

def add_commands(main_cli):
    @main_cli.group()
    def extension():
        """Extension commands."""
        pass
    
    @extension.command()
    def generate():
        """Generate something."""
        pass
```

## Documentation Coordination

### Documentation Updates

- **Feature branches**: Update relevant docs
- **Release branches**: Complete documentation review
- **Hotfix branches**: Update only if user-facing changes

### Documentation Deployment

Documentation is automatically deployed when:
- Code is pushed to tracked branches
- Release tags are created
- Documentation-only changes are made

See [Documentation Workflow Guide](documentation-workflow.md) for details.

## Collaboration

### Pull Request Process

1. **Create branch** from appropriate base
2. **Implement changes** with tests
3. **Update documentation** if needed
4. **Run tests locally**
5. **Create Pull Request**
6. **Address review feedback**
7. **Merge after approval**

### Issue Management

- **Bug reports**: Use bug report template
- **Feature requests**: Use feature request template
- **Questions**: Use discussions instead of issues
- **Security issues**: Use security policy

### Communication

- **Discussions**: General questions and ideas
- **Issues**: Bug reports and feature requests
- **Pull Requests**: Code changes and reviews
- **Releases**: Announcements and changelogs

## Advanced Workflows

### Multiple Version Support

```bash
# Create maintenance branch for long-term support
git checkout v0.15.3  # Latest 0.15.x version
git checkout -b maint/0.15.x
git push origin maint/0.15.x

# Apply critical fixes to maintenance branch
git checkout maint/0.15.x
git cherry-pick <commit-hash>  # Cherry-pick from main/hotfix
git tag v0.15.4 -m "maintenance: backport critical fix"
git push origin v0.15.4

# Maintain multiple versions simultaneously
# 0.15.x - Long-term support (critical fixes only)
# 0.16.x - Current stable (patches and fixes)
# 0.17.x - Development (new features)
```

**Maintenance strategy**:
- **LTS versions**: Critical security fixes only
- **Current stable**: Bug fixes and patches
- **Development**: New features and improvements

### Extension Release Coordination

```bash
# Release core and extensions together
git tag v0.16.0
git push origin v0.16.0

# Update extensions
cd ../half-orm-dev
git tag v0.16.0
git push origin v0.16.0
```

## Troubleshooting

### Common Issues

**Tests failing locally but passing on CI:**
- Check Python version differences
- Verify database setup
- Review environment variables

**Version conflicts:**
- Ensure all version files are updated
- Check git tags are correct
- Verify PyPI package metadata

**Extension not discovered:**
- Check package naming convention
- Verify cli_extension.py exists
- Ensure proper installation

## Best Practices

1. **Always run tests** before pushing
2. **Write meaningful commit messages**
3. **Keep changes focused** and atomic
4. **Update documentation** with code changes
5. **Use semantic versioning** consistently
6. **Coordinate releases** across extensions
7. **Maintain backward compatibility** when possible
8. **Document breaking changes** clearly

## Tools and Scripts

### Development Setup

```bash
# Clone repository
git clone https://github.com/collorg/halfORM.git
cd halfORM

# Install in development mode
pip install -e .
pip install -r requirements-dev.txt

# Run tests
pytest
```

### Release Scripts

```bash
# Build and test package
python -m build
python -m twine check dist/*

# Local installation test
pip install dist/half_orm-0.16.0-py3-none-any.whl
```

This workflow ensures consistent, high-quality releases while maintaining flexibility for different development needs and coordination with the documentation system.