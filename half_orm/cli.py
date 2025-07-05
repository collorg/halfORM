#!/usr/bin/env python3
"""
halfORM unified command-line interface

Discovers and integrates all halfORM extensions into a single CLI.
Extensions are discovered automatically based on package naming convention.

Usage:
    half_orm --help                 # Show all available commands
    half_orm dev new my_project     # Use half-orm-dev extension
    half_orm litestar generate      # Use half-orm-litestar-api extension
"""

import sys
import importlib
from typing import Dict, Any, Optional
import click

# Modern import to replace pkg_resources
try:
    from importlib.metadata import distributions, version
except ImportError:
    # Fallback for Python < 3.8
    from importlib_metadata import distributions, version


def get_distribution_name(dist) -> Optional[str]:
    """
    Get distribution name in a robust way.
    
    Args:
        dist: Distribution object from importlib.metadata
        
    Returns:
        Package name or None if not found
    """
    try:
        # Try different methods to access the name
        if hasattr(dist, 'metadata'):
            # Modern method
            return dist.metadata.get('Name') or dist.metadata.get('name')
        elif hasattr(dist, 'name'):
            # Fallback
            return dist.name
        else:
            return None
    except Exception:
        return None


def get_extension_name_from_package(package_name: str) -> str:
    """
    Extract extension name from package name.
    
    Args:
        package_name: Package name (e.g., 'half-orm-dev')
        
    Returns:
        Extension name (e.g., 'dev')
    """
    if package_name.startswith('half-orm-'):
        return package_name.replace('half-orm-', '')
    return package_name

import half_orm


def discover_extensions() -> Dict[str, Any]:
    """
    Discover all installed halfORM extensions.
    
    Looks for packages matching 'half-orm-*' pattern and tries to import
    their cli_extension module for CLI integration.
    
    Returns:
        Dict mapping extension names to their cli_extension modules
    """
    extensions = {}
    
    # Use importlib.metadata instead of pkg_resources
    for dist in distributions():
        try:
            # Get package name robustly
            package_name = get_distribution_name(dist)
            if not package_name or not package_name.startswith('half-orm-'):
                continue
                
            # Convert package name to module name
            module_name = package_name.replace('-', '_')
            
            # Try to import the CLI extension interface
            extension_module = importlib.import_module(f'{module_name}.cli_extension')
            
            # Verify the extension has the required interface
            if hasattr(extension_module, 'add_commands'):
                # Extract extension name (remove 'half-orm-' prefix)
                extension_name = get_extension_name_from_package(package_name)
                
                # Get version robustly
                try:
                    dist_version = dist.version
                except Exception:
                    dist_version = get_package_version(package_name)
                
                extensions[extension_name] = {
                    'module': extension_module,
                    'package_name': package_name,
                    'version': dist_version,
                    'metadata': getattr(extension_module, 'EXTENSION_INFO', {})
                }
                        
        except ImportError:
            # Extension doesn't have CLI integration - skip silently
            continue
        except Exception as e:
            # Skip distributions that can't be processed
            continue
    
    return extensions


def get_extension_info(extensions: Dict[str, Any]) -> str:
    """
    Generate formatted information about discovered extensions.
    
    Args:
        extensions: Dictionary of discovered extensions
        
    Returns:
        Formatted string with extension information
    """
    if not extensions:
        return "No extensions installed. Try: pip install half-orm-dev"
    
    info = ["Available extensions:"]
    
    for ext_name, ext_data in sorted(extensions.items()):
        metadata = ext_data['metadata']
        version = ext_data['version']
        description = metadata.get('description', 'No description available')
        
        info.append(f"  • {ext_name} v{version}")
        info.append(f"    {description}")
        
        # Show main commands if available
        commands = metadata.get('commands', [])
        if commands:
            info.append(f"    Commands: {', '.join(commands)}")
        
        info.append("")  # Empty line between extensions
    
    return "\n".join(info)


def get_package_version(package_name: str) -> str:
    """
    Get version of a specific package using importlib.metadata.
    
    Args:
        package_name: Name of the package
        
    Returns:
        Version string or 'unknown' if not found
    """
    try:
        return version(package_name)
    except Exception:
        return "unknown"


@click.group(context_settings={'help_option_names': ['-h', '--help']}, invoke_without_command=True)
@click.version_option(version=half_orm.__version__, prog_name='halfORM')
@click.option('--list-extensions', is_flag=True, help='List all installed extensions')
@click.pass_context
def main(ctx, list_extensions):
    """
    halfORM - PostgreSQL-native ORM and development tools
    
    This command provides access to halfORM core functionality and all
    installed extensions through a unified interface.
    
    \b
    Core functionality:
    • Database introspection and relation classes
    • Query building with transparent SQL generation  
    • Transaction management
    • PostgreSQL-native features
    
    \b
    Extensions add additional functionality:
    • half-orm-dev: Development framework and project management
    • half-orm-litestar-api: REST API generation
    • half-orm-admin: Admin interface generation
    • And more...
    
    Install extensions with: pip install half-orm-{extension-name}
    """
    if list_extensions:
        extensions = discover_extensions()
        click.echo(get_extension_info(extensions))
        ctx.exit(0)
    
    # If no subcommand is invoked, show help
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        ctx.exit(0)


@main.command()
@click.argument('database_name')
@click.argument('relation_name', required=False)
def inspect(database_name, relation_name):
    """
    Inspect database structure using halfORM introspection.
    
    DATABASE_NAME: Name of the database to inspect
    RELATION_NAME: Optional specific relation to inspect (schema.table format)
    
    Examples:
        half_orm inspect my_database
        half_orm inspect my_database public.users
    """
    try:
        from half_orm.model import Model
        
        # Connect to database
        model = Model(database_name)
        
        if relation_name:
            # Inspect specific relation
            try:
                relation_class = model.get_relation_class(relation_name)
                click.echo(f"=== {relation_name} ===")
                click.echo(str(relation_class()))
            except Exception as e:
                click.echo(f"❌ Error inspecting {relation_name}: {e}", err=True)
                sys.exit(1)
        else:
            # List all relations
            click.echo(f"=== Database: {database_name} ===")
            relations = list(model._relations())
            
            if not relations:
                click.echo("No relations found in database")
                return
            
            # Group by schema
            schemas = {}
            for relation in relations:
                relation_type, (_, schema, table) = relation
                if schema not in schemas:
                    schemas[schema] = []
                schemas[schema].append((relation_type, table))
            
            # Display grouped by schema
            count_d = {}
            for schema, tables in sorted(schemas.items()):
                rel_type_d = {
                    'r': ("📋", "table"),
                    'v': ("👁️ ", "view"),
                    'p': ("📊", "partioned table"),
                    'm': ("🔗", "materialized view")
                }
                click.echo(f"\n📂 Schema: {schema}")
                for rel_type, table in sorted(tables):
                    if not rel_type in count_d:
                        count_d[rel_type] = 0
                    count_d[rel_type] += 1
                    type_icon = rel_type_d.get(rel_type, ["?"])[0]
                    click.echo(f"  {type_icon} {table}")
            
            click.echo(f"\nTotal: {len(relations)} relations")
            for rel_type in rel_type_d:
                count = count_d.get(rel_type)
                if count:
                    plural = count > 1 and 's' or ''
                    icon, name = rel_type_d[rel_type]
                    click.echo(f"   {icon}: {count} {name}{plural}")
            click.echo("\nUse 'half_orm inspect {db} {schema.table}' for detailed information")
            
    except ImportError:
        click.echo("❌ halfORM core not properly installed", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error connecting to database '{database_name}': {e}", err=True)
        click.echo("💡 Check your database configuration in HALFORM_CONF_DIR", err=True)
        sys.exit(1)


@main.command()
def version():
    """Show detailed version information for halfORM and extensions."""
    click.echo(f"halfORM Core: {half_orm.__version__}")
    
    extensions = discover_extensions()
    if extensions:
        click.echo("\nInstalled Extensions:")
        for ext_name, ext_data in sorted(extensions.items()):
            click.echo(f"  {ext_name}: {ext_data['version']}")
    else:
        click.echo("\nNo extensions installed")
        click.echo("Try: pip install half-orm-dev")


def register_extensions():
    """
    Discover and register all halfORM extensions.
    
    This function is called at module level to automatically integrate
    all discovered extensions into the main CLI.
    """
    extensions = discover_extensions()
    
    for ext_name, ext_data in extensions.items():
        try:
            # Call the extension's add_commands function
            ext_data['module'].add_commands(main)
            
        except Exception as e:
            # Log registration errors but don't crash the entire CLI
            click.echo(f"Warning: Failed to register commands for {ext_name}: {e}", err=True)
            continue


# Auto-register extensions when module is imported
try:
    register_extensions()
except Exception as e:
    # If extension discovery fails completely, still allow core functionality
    click.echo(f"Warning: Extension discovery failed: {e}", err=True)


if __name__ == '__main__':
    main()