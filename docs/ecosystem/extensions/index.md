# halfORM Extensions

halfORM 0.16 introduces a powerful extension system that automatically discovers and integrates additional functionality through the unified `half_orm` CLI.

## How Extensions Work

Extensions are Python packages that follow the `half-orm-*` naming convention and provide CLI integration through a simple discovery mechanism.

### Installation & Discovery

```bash
# Install any halfORM extension
pip install half-orm-extension-name

# Extensions are automatically discovered
half_orm --list-extensions

# Use extension commands immediately
half_orm extension-name command
```

### Extension Architecture

Extensions integrate seamlessly with the halfORM CLI by providing:

- **Auto-discovery**: Packages matching `half-orm-*` pattern
- **CLI integration**: Commands added to the main `half_orm` interface
- **Metadata**: Version, description, and available commands
- **Isolation**: Each extension operates independently

## Official Extensions

Official extensions are maintained by the halfORM team and follow strict quality and compatibility standards.

### ✅ Released

#### half-orm-test-extension
**Purpose**: Demonstration and testing of the extension system  
**Status**: Released v0.1.0  
**Repository**: [collorg/half-orm-test-extension](https://github.com/collorg/half-orm-test-extension)

```bash
# Installation
pip install git+https://github.com/collorg/half-orm-test-extension

# Usage
half_orm test-extension greet
half_orm test-extension status
```

**Commands**:

- `greet` - Simple greeting command
- `status` - Display extension status

---

### 📋 Planned

#### half-orm-dev
**Purpose**: Development tools and project management  
**Status**: Planned  
**Base**: Development starting from [halfORM_dev](https://github.com/collorg/halfORM_dev)

Modern remake of the HOP (halfORM Packager) with enhanced CLI integration and project management features.

#### half-orm-litestar-api
**Purpose**: REST API generation using Litestar framework  
**Status**: Planned  

Fast and modern REST API generation with automatic OpenAPI documentation and high-performance async endpoints.

#### half-orm-admin
**Purpose**: Admin interface generation  
**Status**: Planned  

**Planned Features**:

- Web-based admin interface
- CRUD operations for all models
- User management and permissions
- Custom admin panels

#### half-orm-monitoring
**Purpose**: Observability and monitoring tools  
**Status**: Planned  

**Planned Features**:

- Query performance monitoring
- Database health checks
- Metrics collection and reporting
- Integration with monitoring platforms

## Community Extensions

We welcome community-contributed extensions! Here's how to get started:

### Creating an Extension

1. **Name your package** following the `half-orm-*` convention
2. **Implement discovery** by creating a `cli_extension.py` module
3. **Add CLI commands** using Click framework
4. **Publish to PyPI** for easy installation

### Extension Template

```python
# your_extension/cli_extension.py
import click

def add_commands(main_cli):
    """Required entry point for halfORM extensions."""
    
    @main_cli.group()
    def your_extension():
        """Your extension commands."""
        pass
    
    @your_extension.command()
    def hello():
        """Say hello."""
        click.echo("Hello from your extension!")
```

For a complete working example, see [half-orm-test-extension](https://github.com/collorg/half-orm-test-extension) which demonstrates all the essential patterns for extension development.

### Guidelines for Community Extensions

- **Naming**: Use `half-orm-*` format (e.g., `half-orm-my-feature`)
- **Documentation**: Include clear README with usage examples
- **Testing**: Provide test suite for your extension
- **Compatibility**: Test with multiple halfORM versions
- **Security**: Follow security best practices
- **Licensing**: Use compatible open-source license

### Submitting Extensions

Community extensions can be:

1. **Listed here** by submitting a PR to this documentation
2. **Promoted to official** if they meet quality standards and fill important use cases
3. **Featured** in halfORM blog posts and tutorials

## Extension Development

### Local Development Setup

```bash
# Clone extension template
git clone https://github.com/collorg/half-orm-extension-template
cd half-orm-extension-template

# Install in development mode
pip install -e .

# Test extension discovery
half_orm --list-extensions
```

### Testing Extensions

```bash
# Test your extension
half_orm your-extension --help

# Run extension tests
pytest tests/

# Test with multiple halfORM versions
tox
```

## Resources

- **[Extension Development Guide](../development/getting-started.md)** - Complete development tutorial
- **[Plugin API Reference](../development/plugin-api.md)** - Technical integration details
- **[halfORM Test Extension](https://github.com/collorg/half-orm-test-extension)** - Reference implementation
- **[GitHub Discussions](https://github.com/collorg/halfORM/discussions)** - Community support

## Getting Help

- **Questions**: [GitHub Discussions](https://github.com/collorg/halfORM/discussions)
- **Bug Reports**: [GitHub Issues](https://github.com/collorg/halfORM/issues)
- **Extension Ideas**: [Extension Request Template](https://github.com/collorg/halfORM/issues/new?template=extension_request.yml)

---

**The halfORM extension system enables a rich ecosystem of tools built on PostgreSQL-first principles. Whether you're using official extensions or building your own, the unified CLI provides a consistent developer experience.**