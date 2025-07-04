#!/usr/bin/env python3
"""
Universal REST API with halfORM and FastAPI
Automatically generates secure read-only endpoints for configured database relations

Usage:
    python instant_api.py <database_name>
    python instant_api.py <database_name> --create-config

Example:
    python instant_api.py blog_tutorial
    python instant_api.py blog_tutorial --create-config

Security:
    - Requires explicit configuration file
    - Read-only operations only (GET endpoints)
    - Column-level access control
    - No default data exposure
"""

import os
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Query, Request
from half_orm.model import Model
from half_orm.null import NULL


class APIConfig:
    """API configuration based on YAML file with INSTANT_API_CONF_DIR support"""
    
    def __init__(self, database_name: str):
        self.database_name = database_name
        self.confdir = os.getenv('INSTANT_API_CONF_DIR', '/etc/half_orm/instant_api')
        self.config_file = Path(self.confdir) / f"{self.database_name}.yml"
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            print(f"INSTANT_API_CONF_DIR={self.confdir}")
            print(f"❌ file {self.config_file} not found!")
            print(f"Check your configuration.")
            return None
        except yaml.YAMLError as exc:
            print(f"❌ Error parsing config file {self.config_file}: {exc}")
            return None
    
    def has_config(self) -> bool:
        """Check if configuration file exists"""
        return self.config is not None
    
    def is_exposed(self, schema: str, relation: str, column: str = None) -> bool:
        """Check if a relation/column is exposed"""
        if not self.has_config():
            return False  # No config = no access
        
        schema_config = self.config.get(schema, {})
        if not schema_config:
            return False
        
        relation_config = schema_config.get(relation, {})
        if not relation_config:
            return False
        
        if column is None:
            return True  # The relation is exposed
        
        # Check if the column is in the list
        return column in relation_config
    
    def get_exposed_columns(self, schema: str, relation: str) -> List[str]:
        """Return the list of exposed columns for a relation"""
        if not self.has_config():
            return []  # No config = no access
        
        return self.config.get(schema, {}).get(relation, [])

class UniversalAPI:
    """Universal REST API for halfORM"""
    
    def __init__(self, database_name: str):
        self.database_name = database_name
        self.model = Model(database_name)
        self.config = APIConfig(database_name)
        
        if not self.config.has_config():
            print(f"❌ ERROR: No configuration file found at {self.config.config_file}")
            print("Create a configuration file to expose database relations.")
            print(f"Run: python instant_api.py {database_name} --create-config")
            sys.exit(1)
        
        # Generate description with available routes
        routes_description = "### Read-only API automatically generated with halfORM\n"
        routes_description += "This is a proof of concept. **Do not use in production**.\n"
        
        if self.config.has_config():
            routes_description += "#### Available endpoints:\n"
            for relation in self.model._relations():
                _, schema_name, relation_name = relation[1]
                if self.config.is_exposed(schema_name, relation_name):
                    exposed_columns = self.config.get_exposed_columns(schema_name, relation_name)
                    if exposed_columns:
                        routes_description += f" - GET **/{schema_name}/{relation_name}** - List {relation_name} records\n\n"
                        routes_description += f" - GET **/{schema_name}/{relation_name}/{{id}}** - Get single {relation_name} record\n\n"
                        routes_description += f"   -  Available fields: {', '.join(exposed_columns)}\n\n"
        else:
            routes_description += "No routes available - configuration required"
        
        self.app = FastAPI(
            title=f"REST API for {database_name}",
            description=routes_description,
            version="1.0.0"
        )

        @self.app.middleware("http")
        async def add_security_headers(request: Request, call_next):
            response = await call_next(request)
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-Forwarded-Proto"] = "https"
            return response

        self._setup_routes()
    
    def _get_relation_class(self, schema: str, relation: str):
        """Get halfORM relation class"""
        if not self.config.is_exposed(schema, relation):
            raise HTTPException(
                status_code=404, 
                detail=f"Relation {schema}.{relation} not exposed"
            )
        
        try:
            return self.model.get_relation_class(f"{schema}.{relation}")
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Relation {schema}.{relation} not found: {str(e)}"
            )
    
    def _filter_columns(self, data: Dict, schema: str, relation: str) -> Dict:
        """Filter columns according to configuration"""
        exposed_columns = self.config.get_exposed_columns(schema, relation)
        
        if not exposed_columns:
            return data  # All columns
        
        return {k: v for k, v in data.items() if k in exposed_columns}
    
    def _build_filters(self, relation_class, filters: Dict[str, Any]) -> Any:
        """Build halfORM filters from query parameters"""
        if not filters:
            return relation_class()
        
        # Convert filters to halfORM constraints
        constraints = {}
        for key, value in filters.items():
            if value is None or value == "":
                continue
            
            # Support operators in key (e.g., age__gt=25)
            if '__' in key:
                field, op = key.split('__', 1)
                if op == 'gt':
                    constraints[field] = ('>', value)
                elif op == 'gte':
                    constraints[field] = ('>=', value)
                elif op == 'lt':
                    constraints[field] = ('<', value)
                elif op == 'lte':
                    constraints[field] = ('<=', value)
                elif op == 'ne':
                    constraints[field] = ('!=', value)
                elif op == 'like':
                    constraints[field] = ('like', f'%{value}%')
                elif op == 'ilike':
                    constraints[field] = ('ilike', f'%{value}%')
                elif op == 'isnull':
                    constraints[field] = NULL if value.lower() == 'true' else ('is not', NULL)
                else:
                    constraints[field] = value
            else:
                constraints[key] = value
        
        return relation_class(**constraints)
    
    def _setup_routes(self):
        """Configure FastAPI routes"""
        
        @self.app.get("/")
        async def root():
            """Root endpoint with API information"""
            if not self.config.has_config():
                return {
                    "error": "No configuration file found",
                    "message": "Create configuration file to expose database relations",
                    "help": "Run with --create-config to generate configuration"
                }
            
            relations = []
            try:
                # List all available relations
                for relation in self.model._relations():
                    _, schema_name, relation_name = relation[1]
                    if self.config.is_exposed(schema_name, relation_name):
                        relations.append(f"{schema_name}.{relation_name}")
            except Exception:
                pass
            
            return {
                "database": self.database_name,
                "exposed_relations": relations,
                "available_endpoints": [
                    "GET /{schema}/{relation} - List records (read-only)",
                    "GET /{schema}/{relation}/{id} - Get one record (read-only)"
                ],
                "note": "Only read operations are available for security reasons"
            }
        
        @self.app.get("/{schema}/{relation}")
        async def list_records(
            schema: str,
            relation: str,
            request: Request,
            limit: Optional[int] = Query(100, ge=1, le=1000),
            offset: Optional[int] = Query(0, ge=0),
            order_by: Optional[str] = Query(None)
        ):
            """List records with filtering and pagination"""
            relation_class = self._get_relation_class(schema, relation)
            
            # Extract filters from query parameters
            filters = {}
            for key, value in request.query_params.items():
                if key not in ['limit', 'offset', 'order_by']:
                    filters[key] = value
            
            # Build query with filters
            query = self._build_filters(relation_class, filters)
            
            # Apply ordering
            if order_by:
                try:
                    query = query.ho_order_by(order_by)
                except Exception:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid order: {order_by}"
                    )
            
            # Pagination
            query = query.ho_limit(limit).ho_offset(offset)
            
            # Execute and filter columns
            try:
                exposed_columns = self.config.get_exposed_columns(schema, relation)
                if exposed_columns:
                    results = list(query.ho_select(*exposed_columns))
                else:
                    # This should not happen if config is properly checked
                    raise HTTPException(status_code=500, detail="No columns configured")
                
                return {
                    "data": results,
                    "count": len(results),
                    "limit": limit,
                    "offset": offset,
                    "total": self._build_filters(relation_class, filters).ho_count()
                }
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/{schema}/{relation}/{record_id}")
        async def get_record(schema: str, relation: str, record_id: int):
            """Get a specific record"""
            relation_class = self._get_relation_class(schema, relation)
            
            try:
                # Assume primary key is 'id'
                record = relation_class(id=record_id)
                if record.ho_is_empty():
                    raise HTTPException(
                        status_code=404,
                        detail=f"Record {record_id} not found"
                    )
                
                data = record.ho_get()
                return self._filter_columns(dict(data), schema, relation)
            
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/{schema}/{relation}")
        async def create_record_not_allowed(schema: str, relation: str):
            """Create operations are not available for security reasons"""
            raise HTTPException(
                status_code=405,
                detail="POST operations are not allowed. This is a read-only API for security reasons."
            )
        
        @self.app.put("/{schema}/{relation}/{record_id}")
        async def update_record_not_allowed(schema: str, relation: str, record_id: int):
            """Update operations are not available for security reasons"""
            raise HTTPException(
                status_code=405,
                detail="PUT operations are not allowed. This is a read-only API for security reasons."
            )
        
        @self.app.delete("/{schema}/{relation}/{record_id}")
        async def delete_record_not_allowed(schema: str, relation: str, record_id: int):
            """Delete operations are not available for security reasons"""
            raise HTTPException(
                status_code=405,
                detail="DELETE operations are not allowed. This is a read-only API for security reasons."
            )


def create_config_from_database(database_name: str):
    """Create configuration file by introspecting the database schema"""
    try:
        model = Model(database_name)
        confdir = os.getenv('INSTANT_API_CONF_DIR', '/etc/half_orm/instant_api')
        config_file = Path(confdir) / f"{database_name}.yml"
        
        # Create directory if it doesn't exist
        Path(confdir).mkdir(parents=True, exist_ok=True)
        
        # Check if config already exists
        if config_file.exists():
            print(f"Configuration file {config_file} already exists")
            response = input("Overwrite? (y/N): ")
            if response.lower() != 'y':
                print("Cancelled.")
                return
        
        print(f"🔍 Introspecting database {database_name}...")
        
        schemas = {}
        # Parse database relations using model._relations()
        for relation in model._relations():
            _, schema_name, relation_name = relation[1]
                    
            # Get relation class to inspect columns
            try:
                relation_class = model.get_relation_class(f"{schema_name}.{relation_name}")
                relation_instance = relation_class()
                columns = []
                # Extract column names using _ho_fields
                for column_name in relation_instance._ho_fields:
                    columns.append(column_name)
                
                # Add to schemas dict
                if schema_name not in schemas:
                    schemas[schema_name] = {}
                schemas[schema_name][relation_name] = columns
                
            except Exception as e:
                print(f"Warning: Could not introspect {schema_name}.{relation_name}: {e}")
                continue
        
        # Generate YAML config with all lines commented
        yaml_content = f"# Configuration for {database_name} database\n"
        yaml_content += f"# Generated by introspection - uncomment lines to expose data\n"
        yaml_content += f"# INSTANT_API_CONF_DIR={confdir}\n\n"
        
        for schema_name, relations in schemas.items():
            yaml_content += f"# {schema_name}:\n"
            for relation_name, columns in relations.items():
                yaml_content += f"#   {relation_name}:\n"
                for column in columns:
                    yaml_content += f"#     - {column}\n"
                yaml_content += "#\n"
            yaml_content += "\n"
                
        # Write config file
        with open(config_file, 'w') as f:
            f.write(yaml_content)
        
        print(f"✅ Created configuration file: {config_file}")
        print(f"📋 Found {len(schemas)} schemas with {sum(len(relations) for relations in schemas.values())} relations")
        print(f"📝 Edit the file and uncomment the lines for data you want to expose")
        print(f"💡 Example: Remove the '#' from lines under blog.author to expose author data")
        
    except Exception as e:
        print(f"❌ Error creating config from database: {e}")
        print(f"Make sure database '{database_name}' exists and is accessible")
        sys.exit(1)

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python instant_api.py <database_name> [--port PORT] [--host HOST]")
        print("       python instant_api.py <database_name> --create-config")
        print("")
        print("Examples:")
        print("  python instant_api.py blog_tutorial")
        print("  python instant_api.py blog_tutorial --create-config")
        print("  python instant_api.py blog_tutorial --port 8001 --host 127.0.0.1")
        print("")
        print("Environment Variables:")
        print("  INSTANT_API_CONF_DIR - Configuration directory (default: /etc/half_orm/instant_api)")
        print("  INSTANT_API_PORT     - Default port (default: 8000)")
        print("  INSTANT_API_HOST     - Default host (default: 127.0.0.1)")
        sys.exit(1)
    
    database_name = sys.argv[1]
    
    # Check for --create-config
    if len(sys.argv) > 2 and sys.argv[2] == "--create-config":
        create_config_from_database(database_name)
        return
        
    # Parse other arguments
    port = int(os.getenv('INSTANT_API_PORT', 8000))
    host = os.getenv('INSTANT_API_HOST', '127.0.0.1')
    
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == '--port' and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])
            i += 2
        elif arg == '--host' and i + 1 < len(sys.argv):
            host = sys.argv[i + 1]
            i += 2
        else:
            print(f"Unknown argument: {arg}")
            sys.exit(1)
    
    print(f"🚀 Starting Universal REST API for database: {database_name}")
    
    # Show configuration info
    confdir = os.getenv('INSTANT_API_CONF_DIR', '/etc/half_orm/instant_api')
    print(f"📋 Config directory: {confdir}")
    print(f"📋 Looking for: {database_name}.yml")
    
    print(f"🌐 API will be available at: http://{host}:{port}")
    print(f"📖 API documentation at: http://{host}:{port}/docs")
    print(f"✅ Read-only API starting...")
    
    # Create and run the API
    api = UniversalAPI(database_name)

    uvicorn.run(api.app, host=host, port=port)


if __name__ == "__main__":
    import uvicorn
    main()