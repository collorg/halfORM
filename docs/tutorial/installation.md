# Chapter 1: Installation

In this chapter, you'll install halfORM and verify it works with your PostgreSQL database. We'll keep it simple and get you up and running quickly!

## Prerequisites

Before installing halfORM, ensure you have:

### System Requirements
- **Python 3.7+** (3.9+ recommended)
- **PostgreSQL 9.6+** (13+ recommended) with peer authentication for `$USER` on development environment
- **psycopg2** (installed automatically with halfORM)

!!! tip "Don't have PostgreSQL?"
    **Quick setup options:**
    
    - **Docker**: `docker run --name postgres-tutorial -e POSTGRES_PASSWORD=tutorial -d -p 5432:5432 postgres:13`
    - **Local install**: [PostgreSQL Downloads](https://www.postgresql.org/download/)
    - **Cloud**: [ElephantSQL](https://www.elephantsql.com/) (free tier), [Supabase](https://supabase.com/), AWS RDS

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
python -m half_orm
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
python -m half_orm
```

## Quick Test with Default PostgreSQL

Let's verify halfORM works with your PostgreSQL installation using the built-in diagnostic tool.

### One-Command Test

halfORM includes a built-in diagnostic tool that tests your installation and database connections:

```bash
# Test halfORM installation and database access
python -m half_orm
```

Expected output:
```
[halfORM] version 0.15.1
- HALFORM_CONF_DIR=/home/user/.half_orm
✅ Connected to template1 database (default setup)
```

This tests:

- ✅ halfORM installation and version
- ✅ Configuration directory location  
- ✅ Default peer authentication with template1
- ✅ Any configured database connections

### What the Test Does

The diagnostic tool automatically:

1. **Tests template1 connection** using peer authentication (no config needed)
2. **Scans your config directory** for database connection files
3. **Tests each configured database** and reports status
4. **Shows helpful error messages** if something isn't working

### Default PostgreSQL Configuration

This works because most PostgreSQL installations include:

```
# in pg_hba.conf
local   all             all                                     peer
```

This allows your system user to connect to any database without a password assuming there is a role
with the correponding name in PostgreSQL. Otherwise you will get the following result:

```
[halfORM] version 0.15.1
- HALFORM_CONF_DIR=/etc/half_orm
HOP WARNING: No config file '/etc/half_orm/template1'.
	 Trying peer authentication for 'nopgaccess'.
❌ connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: FATAL:  role "nopgaccess" does not exist
```

## Database Configuration (Optional)

For production use or when you need to connect to specific databases, halfORM uses configuration files. This section shows you how to set them up, but **it's not required for the tutorial**.

### When You Need Configuration Files

- Connecting to databases other than `template1`
- Using different usernames or passwords
- Connecting to remote databases
- Production deployments

### Basic Configuration Setup

If you want to set up configuration files:

```bash
# Create configuration directory
mkdir ~/.half_orm
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

For local development with trusted authentication:

```ini title="~/.half_orm/my_local_db"
[database]
name = my_local_db
# user defaults to current system user
# no password needed with peer authentication
host = localhost
port = 5432
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
- Verify Python path: `python -c "import sys; print(sys.path)"`

#### PostgreSQL Connection Failed
```
psycopg2.OperationalError: could not connect to server
```

**Solutions:**
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Check PostgreSQL is accepting connections: `psql template1`
- Ensure your user can connect: `psql -U $(whoami) template1`

#### Permission Denied
```
psycopg2.errors.InsufficientPrivilege: permission denied
```

**Solutions:**
- Check `pg_hba.conf` has peer authentication enabled
- Ensure your system user exists in PostgreSQL: `createuser $(whoami)`
- Try connecting manually first: `psql template1`

### Getting Help

If you're still having issues:

1. **Check PostgreSQL is running**: `sudo systemctl status postgresql`
2. **Test manual connection**: `psql template1`
3. **Search existing issues** on [GitHub](https://github.com/collorg/halfORM/issues)
4. **Ask for help** in [GitHub Discussions](https://github.com/collorg/halfORM/discussions)

## What's Next?

Congratulations! You now have:

- ✅ halfORM installed and working
- ✅ Verified connection to PostgreSQL
- ✅ Understanding of basic configuration

In the next chapter, [First Steps](first-steps.md), you'll:

- Set up a complete tutorial database with sample data
- Explore database schemas and tables
- Perform your first CRUD operations
- Learn halfORM's core concepts and syntax

The tutorial database setup has been moved to Chapter 2 to keep this installation chapter focused and simple.

---

**Ready to continue?** Let's move on to [Chapter 2: First Steps](first-steps.md) where we'll create a proper tutorial database and start exploring halfORM's features!