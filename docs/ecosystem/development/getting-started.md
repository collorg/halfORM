# Getting Started with Extension Development

This guide walks you through creating your first halfORM extension that integrates with the `hop` command. You'll learn the basics of the plugin system and build a simple but functional extension.

!!! info "Prerequisites"
    - Familiarity with Python packaging (`setup.py`, `pip install`)
    - Basic understanding of [Click](https://click.palletsprojects.com/) for command-line interfaces
    - Knowledge of halfORM fundamentals ([Quick Start](../../quick-start.md))
    - halfORM_dev installed (`pip install half-orm-dev`)

## What We'll Build

We'll create `half-orm-hello`, a simple extension that demonstrates:
- Plugin discovery and registration
- Integration with `hop` commands
- Access to the current halfORM project context
- Extension configuration and metadata

The final result will provide these commands:
```bash
hop hello greet --name "World"     # Prints "Hello, World!"
hop hello status                   # Shows project information
hop hello config                   # Manages extension settings
```

## Project Setup

### 1. Create Extension Project Structure

```bash
mkdir half-orm-hello
cd half-orm-hello

# Create the standard extension structure
mkdir -p half_orm_hello
touch half_orm_hello/__init__.py
touch half_orm_hello/hop_extension.py
touch setup.py
touch README.md
```

Your structure should look like:
```
half-orm-hello/
├── half_orm_hello/
│   ├── __init__.py
│   └── hop_extension.py    # Required: hop integration
├── setup.py
└── README.md
```

### 2. Package Configuration

Create `setup.py` with the standard extension format:

```python
from setuptools import setup, find_packages

setup(
    name='half-orm-hello',
    version='0.1.0',
    description='Hello World extension for halfORM',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Your Name',
    author_email='your.email@example.com',
    url='https://github.com/yourusername/half-orm-hello',
    license='GPL-3.0',
    packages=find_packages(),
    install_requires=[
        'half-orm>=0.15.0',
        'half-orm-dev>=0.1.0',  # Required for hop integration
        'click>=8.0.0',         # For command-line interface
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Database',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.8',
)
```

## Core Extension Implementation

### 3. Extension Entry Point

Create `half_orm_hello/hop_extension.py` - this is the **required** integration point:

```python
"""
hop extension integration for half-orm-hello

This module provides the entry point for the halfORM ecosystem plugin system.
The add_commands() function is called automatically when the extension is discovered.
"""

import click
from half_orm_dev.repo import Repo


def add_commands(hop_main_group):
    """
    Required entry point for halfORM extensions.
    
    This function is called automatically by hop's plugin discovery system.
    It should add command groups to the main hop CLI.
    
    Args:
        hop_main_group: The main Click group for the hop command
    """
    
    @click.group()
    def hello():
        """Hello World extension commands"""
        pass
    
    @hello.command()
    @click.option('--name', default='halfORM', help='Name to greet')
    @click.option('--uppercase', is_flag=True, help='Use uppercase')
    def greet(name, uppercase):
        """Greet someone with a friendly message"""
        message = f"Hello, {name}!"
        if uppercase:
            message = message.upper()
        click.echo(message)
    
    @hello.command()
    def status():
        """Show current project status"""
        repo = Repo()
        
        if not repo.checked:
            click.echo("❌ Not in a halfORM project directory")
            return
        
        click.echo("✅ halfORM Project Information:")
        click.echo(f"   📦 Project: {repo.name}")
        click.echo(f"   📁 Base directory: {repo.base_dir}")
        
        if hasattr(repo, 'database') and repo.database:
            click.echo(f"   🗄️  Database: {repo.database.model.database}")
            
            # Count relations
            try:
                relations = list(repo.database.model._relations())
                click.echo(f"   📊 Relations: {len(relations)} tables/views")
            except Exception as e:
                click.echo(f"   ⚠️  Database connection issue: {e}")
    
    @hello.command()
    @click.option('--set', 'set_value', nargs=2, help='Set configuration key=value')
    @click.option('--get', 'get_key', help='Get configuration value')
    @click.option('--list', 'list_all', is_flag=True, help='List all configuration')
    def config(set_value, get_key, list_all):
        """Manage extension configuration"""
        # Simple configuration example (in real extension, use proper config storage)
        import os
        config_file = os.path.expanduser("~/.half_orm_hello_config")
        
        if set_value:
            key, value = set_value
            # Save configuration (simplified example)
            with open(config_file, 'a') as f:
                f.write(f"{key}={value}\n")
            click.echo(f"✅ Set {key} = {value}")
            
        elif get_key:
            # Read configuration (simplified example)
            try:
                with open(config_file, 'r') as f:
                    for line in f:
                        if line.startswith(f"{get_key}="):
                            value = line.split('=', 1)[1].strip()
                            click.echo(f"{get_key} = {value}")
                            return
                click.echo(f"❌ Key '{get_key}' not found")
            except FileNotFoundError:
                click.echo(f"❌ Key '{get_key}' not found (no config file)")
                
        elif list_all:
            try:
                with open(config_file, 'r') as f:
                    click.echo("📋 Configuration:")
                    for line in f:
                        if '=' in line:
                            click.echo(f"   {line.strip()}")
            except FileNotFoundError:
                click.echo("📋 No configuration found")
        else:
            click.echo("Use --set, --get, or --list to manage configuration")
    
    # Register the command group with hop
    hop_main_group.add_command(hello)


# Extension metadata (optional but recommended)
EXTENSION_INFO = {
    'name': 'hello',
    'version': '0.1.0',
    'description': 'Hello World extension demonstrating halfORM plugin system',
    'commands': ['hello'],
    'author': 'halfORM Team',
    'url': 'https://github.com/collorg/half-orm-hello'
}
```

### 4. Extension Package Initialization

Update `half_orm_hello/__init__.py`:

```python
"""
half-orm-hello: A Hello World extension for halfORM

This package demonstrates how to create extensions for the halfORM ecosystem.
"""

__version__ = '0.1.0'
__author__ = 'Your Name'

# Import main functionality if needed
from .hop_extension import EXTENSION_INFO

__all__ = ['EXTENSION_INFO']
```

## Testing Your Extension

### 5. Install in Development Mode

```bash
# Install your extension in development mode
pip install -e .

# Verify hop discovers your extension
hop --help
```

You should see your `hello` command listed:
```
Commands:
  hello    Hello World extension commands
  new      Creates a new hop project named <package_name>.
  # ... other hop commands
```

### 6. Test Extension Commands

```bash
# Test the greet command
hop hello greet
# Output: Hello, halfORM!

hop hello greet --name "Developer" --uppercase
# Output: HELLO, DEVELOPER!

# Test status (outside a hop project)
hop hello status
# Output: ❌ Not in a halfORM project directory

# Create a test project and try again
hop new test_project --devel
cd test_project
hop hello status
# Output: ✅ halfORM Project Information...

# Test configuration
hop hello config --set greeting "Bonjour"
hop hello config --get greeting
# Output: greeting = Bonjour

hop hello config --list
# Output: 📋 Configuration:
#            greeting=Bonjour
```

## Understanding the Plugin System

### How Discovery Works

halfORM_dev uses a simple but effective discovery mechanism:

1. **Package Scanning**: Looks for installed packages matching `half-orm-*`
2. **Module Import**: Tries to import `{package_name}.hop_extension`
3. **Function Call**: Calls `add_commands(hop_main_group)` if it exists
4. **Integration**: Your commands become part of the hop CLI

### Extension Loading Sequence

```python
# In half_orm_dev/hop.py (simplified)
def discover_extensions():
    extensions = {}
    for dist in pkg_resources.working_set:
        if dist.project_name.startswith('half-orm-') and dist.project_name != 'half-orm-dev':
            try:
                module_name = dist.project_name.replace('-', '_')
                module = importlib.import_module(f'{module_name}.hop_extension')
                if hasattr(module, 'add_commands'):
                    extensions[dist.project_name] = module
            except ImportError:
                continue
    return extensions

# Your add_commands() function gets called here
for ext_name, ext_module in extensions.items():
    ext_module.add_commands(main_group)
```

### Access to hop Context

Your extension can access the current hop project context:

```python
from half_orm_dev.repo import Repo

def some_command():
    repo = Repo()
    
    # Check if we're in a hop project
    if not repo.checked:
        click.echo("Not in a hop project")
        return
    
    # Access project information
    project_name = repo.name
    base_directory = repo.base_dir
    
    # Access database if available
    if repo.database:
        model = repo.database.model
        # Use halfORM functionality
        relations = list(model._relations())
```

## Best Practices

### Command Organization

```python
# ✅ Good: Organize related commands in groups
@click.group()
def myextension():
    """My extension commands"""
    pass

@myextension.group()
def database():
    """Database-related commands"""
    pass

@myextension.group()  
def api():
    """API-related commands"""
    pass

# Results in: hop myextension database init, hop myextension api generate, etc.
```

### Error Handling

```python
# ✅ Good: Handle errors gracefully
@hello.command()
def risky_operation():
    try:
        repo = Repo()
        if not repo.checked:
            click.echo("❌ Not in a halfORM project", err=True)
            raise click.Abort()
        
        # Your logic here
        result = some_operation()
        click.echo(f"✅ Success: {result}")
        
    except SomeSpecificError as e:
        click.echo(f"❌ Operation failed: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        click.echo("Please report this issue", err=True)
        raise click.Abort()
```

### Configuration Management

```python
# ✅ Good: Use proper configuration storage
import os
import json
from pathlib import Path

def get_config_path():
    """Get extension configuration file path"""
    config_dir = Path.home() / '.half_orm' / 'extensions' / 'hello'
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / 'config.json'

def load_config():
    """Load extension configuration"""
    config_path = get_config_path()
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    return {}

def save_config(config):
    """Save extension configuration"""
    config_path = get_config_path()
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
```

## Next Steps

Congratulations! You've created your first halfORM extension. Here's what to explore next:

### 1. Enhanced Functionality
- **[Plugin API Reference](plugin-api.md)** - Learn advanced integration patterns
- **[Testing Guide](testing.md)** - Add comprehensive tests to your extension
- **Database Integration** - Use halfORM's full power in your extension

### 2. Real-World Examples
Study existing extensions:
- **half-orm-litestar-api** - Complex API generation
- **half-orm-instant-api** - Database introspection and configuration

### 3. Distribution
- **[Publishing Guide](publishing.md)** - Share your extension with the community
- **GitHub Actions** - Set up CI/CD for your extension
- **Documentation** - Create comprehensive user guides

### 4. Advanced Topics
- **Hooks and Events** - Integrate with hop's lifecycle events
- **Configuration Management** - Advanced settings and user preferences  
- **Performance** - Optimize for large projects
- **Error Recovery** - Handle edge cases gracefully

## Common Issues and Solutions

### Extension Not Discovered

**Problem**: `hop --help` doesn't show your extension commands

**Solutions**:
1. Check package name starts with `half-orm-`
2. Verify `hop_extension.py` exists and has `add_commands()` function
3. Ensure extension is installed: `pip list | grep half-orm-hello`
4. Check for import errors: `python -c "import half_orm_hello.hop_extension"`

### Import Errors

**Problem**: Extension fails to load with import errors

**Solutions**:
1. Check dependencies in `setup.py`
2. Verify module paths are correct
3. Test imports manually: `python -c "from half_orm_hello import hop_extension"`

### Command Conflicts

**Problem**: Command names conflict with other extensions

**Solutions**:
1. Use descriptive, unique command group names
2. Namespace your commands: `hop myextension subcommand`
3. Check existing extensions for naming conflicts

## Resources

- **[halfORM Fundamentals](../../fundamentals.md)** - Core ORM concepts
- **[Click Documentation](https://click.palletsprojects.com/)** - Command-line interface framework
- **[Plugin API Reference](plugin-api.md)** - Advanced integration patterns
- **[Extension Examples](https://github.com/collorg/halfORM-examples)** - Real-world extension code

## Community

- **Questions**: [GitHub Discussions](https://github.com/collorg/halfORM/discussions)
- **Bug Reports**: [GitHub Issues](https://github.com/collorg/halfORM/issues)
- **Extension Ideas**: [Community Extensions](https://github.com/collorg/halfORM/discussions/categories/extensions)

---

*Ready to build something more complex? Continue to the [Plugin API Reference](plugin-api.md) for advanced integration patterns.*

