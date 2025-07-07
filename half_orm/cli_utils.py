"""
halfORM CLI utilities for extensions

Provides common functionality that extensions can use to integrate 
with the halfORM CLI system.
"""

from typing import Optional


def get_extension_name_from_module(module_name: str) -> str:
    """
    Extract extension name from module name.
    
    Args:
        module_name: The __name__ of the extension module
        
    Returns:
        The clean extension name (e.g., 'inspect', 'test-extension')
        
    Examples:
        'half_orm_inspect.cli_extension' -> 'inspect'
        'half_orm_test_extension.cli_extension' -> 'test-extension'
    """
    # Extract the main package name from module hierarchy
    if '.' in module_name:
        package_name = module_name.split('.')[0]
    else:
        package_name = module_name
    
    # Convert underscores back to hyphens and remove half_orm prefix
    if package_name.startswith('half_orm_'):
        clean_name = package_name.replace('half_orm_', '')
        # Convert underscores to hyphens for multi-word extensions
        return clean_name.replace('_', '-')
    
    return package_name


def get_package_metadata(module):
    """
    Extract package metadata from module.
    
    Args:
        module: The extension module
        
    Returns:
        dict: Package metadata (version, author, description, etc.)
    """
    try:
        # Modern import to replace pkg_resources
        try:
            from importlib.metadata import metadata
        except ImportError:
            # Fallback for Python < 3.8
            from importlib_metadata import metadata
            
        # Convert module name to package name
        module_name = module.__name__
        if '.' in module_name:
            package_name = module_name.split('.')[0]
        else:
            package_name = module_name
            
        # Convert underscores back to hyphens for package lookup
        package_name = package_name.replace('_', '-')
        
        # Get package metadata
        pkg_metadata = metadata(package_name)
        
        return {
            'version': pkg_metadata.get('Version', 'unknown'),
            'author': pkg_metadata.get('Author', 'unknown'),
            'description': pkg_metadata.get('Summary', pkg_metadata.get('Description', '')),
            'package_name': package_name
        }
        
    except Exception:
        # Fallback if metadata not available
        return {
            'version': 'unknown',
            'author': 'unknown', 
            'description': '',
            'package_name': 'unknown'
        }


def get_extension_commands(extension_group):
    """
    Auto-discover commands from a Click group.
    
    Args:
        extension_group: Click group object
        
    Returns:
        list: List of command names
    """
    try:
        return list(extension_group.commands.keys())
    except Exception:
        return []


def create_and_register_extension(main_group, module, description: Optional[str] = None):
    """
    Create and register an extension group as a decorator.
    
    Args:
        main_group: The main halfORM CLI group
        module: The extension module (use sys.modules[__name__])
        description: Optional description override. If None, uses module docstring or package description
        
    Example:
        import sys
        
        @create_and_register_extension(main_group, sys.modules[__name__])
        def my_extension_commands():
            '''Extension description from docstring'''
            pass
            
        @my_extension_commands.command()
        def some_command():
            pass
    """
    import click
    
    # Extract extension name from the module
    extension_name = get_extension_name_from_module(module.__name__)
    
    def decorator(func):
        # Use description parameter, or function docstring, or package description
        if description is None:
            # Try function docstring first
            func_description = func.__doc__.strip() if func.__doc__ else ''
            if not func_description:
                # Fallback to package description
                metadata = get_package_metadata(module)
                func_description = metadata.get('description', '')
        else:
            func_description = description
            
        # Create the Click group
        extension_group = click.group(name=extension_name, help=func_description)(func)
        # Register it with the main group
        main_group.add_command(extension_group)
        # Return the group so commands can be added to it
        return extension_group
    
    return decorator
