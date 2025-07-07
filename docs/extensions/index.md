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
- **Version compatibility**: Extensions must match halfORM core major.minor version

### Security Model

halfORM has a built-in security model for extensions:

- **Official extensions** - Automatically trusted and loaded
- **Community extensions** - Require user approval on first use
- **Trusted extensions** - Previously approved versions
- **Version compatibility** - Extensions must match core major.minor version

```bash
# Trust a community extension version
half_orm my-extension command  # Shows security prompt first time

# Remove trust for an extension
half_orm --untrust my-extension
```

## Available Extensions

### ✅ Official Extensions

#### half-orm-test-extension
**Purpose**: Demonstration and testing of the extension system  
**Repository**: [collorg/half-orm-test-extension](https://github.com/collorg/half-orm-test-extension)

```bash
# Installation
pip install git+https://github.com/collorg/half-orm-test-extension

# Usage
half_orm test-extension greet --name "World"
half_orm test-extension status
```

#### half-orm-inspect
**Purpose**: Enhanced database inspection and exploration  
**Status**: In development

```bash
# When available
pip install half-orm-inspect

# Usage  
half_orm inspect my_database
half_orm inspect my_database public.users --details
```

### 📋 More Extensions in Development

Official extensions are maintained by the halfORM team and follow strict quality and compatibility standards. More extensions are in active development to support various use cases like API generation, admin interfaces, and monitoring tools.

## Creating Extensions

Building halfORM extensions is straightforward with the new simplified architecture:

### Simple Extension Template

```python
# your_extension/cli_extension.py
import sys
import click
from half_orm.cli_utils import create_and_register_extension

def add_commands(main_group):
    """Required entry point for halfORM extensions."""
    
    @create_and_register_extension(main_group, sys.modules[__name__])
    def your_extension():
        """Your extension description"""
        pass
    
    @your_extension.command()
    @click.option('--name', default='World', help='Name to greet')
    def hello(name):
        """Say hello command"""
        click.echo(f"Hello, {name}!")
    
    @your_extension.command()
    def status():
        """Show extension status"""
        from half_orm.cli_utils import get_package_metadata, get_extension_commands
        
        metadata = get_package_metadata(sys.modules[__name__])
        commands = get_extension_commands(your_extension)
        
        click.echo(f"Extension: {metadata['package_name']}")
        click.echo(f"Version: {metadata['version']}")
        click.echo(f"Commands: {', '.join(commands)}")
```

### Key Features

- **Auto-registration**: Use `@create_and_register_extension` decorator
- **Automatic metadata**: Version, description, and commands discovered automatically
- **Security model**: Official extensions trusted, community extensions require approval
- **Version compatibility**: Must match halfORM core major.minor version

For a complete working example, see [half-orm-test-extension](https://github.com/collorg/half-orm-test-extension) which demonstrates all the essential patterns.

## Development Resources

- **[Extension Development Guide](../guides/development/extension-development.md)** - Complete development tutorial
- **[halfORM Development Workflow](../guides/development/development-workflow.md)** - Core development process
- **[Documentation Workflow](../guides/development/documentation-workflow.md)** - Documentation standards

## Community and Support

- **[GitHub Discussions](https://github.com/collorg/halfORM/discussions)** - Ask questions, share ideas
- **[GitHub Issues](https://github.com/collorg/halfORM/issues)** - Report bugs, request features
- **[Extension Ideas](https://github.com/collorg/halfORM/discussions/categories/ideas)** - Propose new extensions

---

**The halfORM extension system brings modular functionality to PostgreSQL development while maintaining security and compatibility.**

Ready to get started? **[Install halfORM →](../quick-start.md)** or **[Create your first extension →](../guides/development/extension-development.md)**