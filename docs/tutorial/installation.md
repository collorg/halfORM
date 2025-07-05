# Chapter 1: Installation

In this chapter, you'll install halfORM and verify it works with your PostgreSQL database. We'll keep it simple and get you up and running quickly!

## Prerequisites

Before installing halfORM, ensure you have:

### System Requirements
- **Python 3.7+** (3.9+ recommended)
- **PostgreSQL 9.6+** (13+ recommended)
- **Basic PostgreSQL access** (peer authentication or configured user)

!!! tip "Don't have PostgreSQL?"
    **Quick setup options:**
    
    - **Docker**: `docker run --name postgres-tutorial -e POSTGRES_PASSWORD=tutorial -d -p 5432:5432 postgres:13`
    - **Local install**: [PostgreSQL Downloads](https://www.postgresql.org/download/)
    - **Cloud**: [ElephantSQL](https://www.elephantsql.com/) (free tier), [Supabase](https://supabase.com/)

## Installing halfORM

### Method 1: pip with virtual environment (Recommended)

```bash
# Create virtual environment
python -m venv halfORM-tutorial
source halfORM-tutorial/bin/activate  # Linux/Mac
# halfORM-tutorial\Scripts\activate  # Windows

# Install halfORM
pip install half_orm

# Verify installation
half_orm version
```

Expected output:
```
halfORM Core: 0.16.0

No Extensions installed
```

!!! tip "Virtual Environment Benefits"
    Using a virtual environment prevents conflicts with other Python packages and makes it easy to reproduce the tutorial environment.

### Method 2: Development Installation

If you want to contribute or use the latest features:

```bash
# Clone the repository
git clone https://github.com/collorg/halfORM.git
cd halfORM

# Install in development mode
pip install -e .

# Verify installation
half_orm version
```

## Quick Test with PostgreSQL

Let's verify halfORM works with your PostgreSQL installation using the built-in diagnostic.

### One-Command Test

```bash
# Test halfORM installation and database access
half_orm inspect template1
```

### Expected Results

**✅ Success (peer authentication working):**
```
=== Database: template1 ===
No relations found in database
```

**❌ Connection issue:**
```
Error: could not connect to server: FATAL: role "username" does not exist
```

### What This Tests

The diagnostic automatically:

- ✅ halfORM installation and CLI
- ✅ PostgreSQL connection
- ✅ Database access permissions
- ✅ Schema inspection capability

## Database Configuration (Optional)

For production use or specific databases, halfORM uses configuration files. This section shows setup, but **it's not required for the tutorial**.

### When You Need Configuration Files

- If you don't have peer authentication access
- Using different usernames or passwords
- Connecting to remote databases
- Production deployments

### Basic Configuration Setup

```bash
# Create configuration directory
mkdir ~/.half_orm

# Set environment variable
export HALFORM_CONF_DIR=~/.half_orm

# Add to shell profile for persistence
echo 'export HALFORM_CONF_DIR=~/.half_orm' >> ~/.bashrc
```

### Example Configuration File

```ini title="~/.half_orm/my_database"
[database]
name = my_database
user = my_user
password = my_password
host = localhost
port = 5432
```

Usage:
```python
from half_orm.model import Model
db = Model('my_database')  # References ~/.half_orm/my_database
```

### Trusted Authentication (No Password)

For local development:

```ini title="~/.half_orm/my_local_db"
[database]
name = my_local_db
```

## Extension Testing (Optional)

Test the new extension system:

```bash
# Install test extension
pip install git+https://github.com/collorg/half-orm-test-extension

# List extensions
half_orm --list-extensions

# Try extension command
half_orm test-extension greet
```

Expected output:
```
Available extensions:
  • test-extension v0.1.0
    Simple test extension for halfORM ecosystem
    Commands: greet, status

Hello, halfORM!
```

## Troubleshooting

### Common Issues

#### halfORM Import Error
```
ModuleNotFoundError: No module named 'half_orm'
```

**Solutions:**
- Check virtual environment is activated
- Install halfORM: `pip install half_orm`
- Verify installation: `half_orm version`

#### PostgreSQL Connection Failed
```
could not connect to server: Connection refused
```

**Solutions:**
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Test manual connection: `psql template1`
- Verify PostgreSQL port: `sudo netstat -tlnp | grep 5432`

#### Permission Denied
```
FATAL: role "username" does not exist
```

**Solutions:**
- Create PostgreSQL user: `sudo -u postgres createuser $(whoami)`
- Grant permissions: `sudo -u postgres psql -c "ALTER USER $(whoami) CREATEDB;"`
- Check `pg_hba.conf` has peer authentication enabled

#### half_orm Not Found
```
half_orm: command not found
```

**Solutions:**
- Ensure virtual environment is activated
- Check PATH includes pip install location
- Reinstall: `pip install --force-reinstall half_orm`

### Getting Help

If you're still having issues:

1. **Check PostgreSQL status**: `sudo systemctl status postgresql`
2. **Test manual connection**: `psql template1`
3. **Verify installation**: `half_orm version`
4. **Search existing issues**: [GitHub Issues](https://github.com/collorg/halfORM/issues)
5. **Ask for help**: [GitHub Discussions](https://github.com/collorg/halfORM/discussions)

### Debug Information

For bug reports, include:

```bash
# System information
half_orm version
python --version
psql --version

# Connection test
half_orm inspect template1

# Extension status
half_orm --list-extensions
```

## What's Next?

Congratulations! You now have:

- ✅ halfORM installed and working
- ✅ Verified connection to PostgreSQL
- ✅ Understanding of basic configuration
- ✅ CLI commands working

In the next chapter, [First Steps](first-steps.md), you'll:

- Set up a complete tutorial database with sample data
- Explore database schemas and tables with the new CLI
- Perform your first CRUD operations
- Learn halfORM's core concepts and syntax

The tutorial database setup is in Chapter 2 to keep this installation chapter focused and simple.

---

**Ready to continue?** Let's move on to [Chapter 2: First Steps](first-steps.md) where we'll create a proper tutorial database and start exploring halfORM's features!