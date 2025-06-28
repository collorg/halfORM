# halfORM Documentation

!!! info "Documentation Version"
    This documentation covers halfORM **0.15.0** (latest stable release).
    For older versions, see the [GitHub releases](https://github.com/collorg/halfORM/releases).

[![PyPI version](https://img.shields.io/pypi/v/half_orm)](https://pypi.org/project/half-orm/)
[![Python versions](https://img.shields.io/badge/Python-%20≥%203.7-blue)](https://www.python.org)
[![PostgreSQL versions](https://img.shields.io/badge/PostgreSQL-%20≥%209.6-blue)](https://www.postgresql.org)
[![License](https://img.shields.io/pypi/l/half_orm?color=green)](https://pypi.org/project/half-orm/)
[![Tests](https://github.com/collorg/halfORM/actions/workflows/python-package.yml/badge.svg)](https://github.com/collorg/halfORM/actions/workflows/python-package.yml)

**The PostgreSQL-native ORM that stays out of your way**

> halfORM lets you keep your database schema in SQL where it belongs, while giving you the comfort of Python for data manipulation. No migrations, no schema conflicts, no ORM fighting — just PostgreSQL and Python working together.

## Overview

halfORM is a lightweight, database-first Object-Relational Mapper designed specifically for PostgreSQL. Unlike traditional ORMs that impose their own schema management, halfORM adapts to your existing database structure, making it perfect for teams that prefer SQL-first development.

**Why halfORM?**

- **🎯 Database-First**: Your PostgreSQL schema is the source of truth
- **🔍 SQL Transparency**: See exactly what queries are generated
- **⚡ Zero Setup**: Connect to existing databases instantly
- **🚀 PostgreSQL Native**: Leverage advanced PostgreSQL features
- **🎨 Custom Classes**: Override with business logic using `@register`

## Key Features

### 🔥 **Instant Database Access**
```python
from half_orm.model import Model

# Connect to your existing database
blog = Model('blog_db')

# Work with your tables immediately
Post = blog.get_relation_class('blog.post')
Author = blog.get_relation_class('blog.author')
```

### 🎨 **Custom Relation Classes**
```python
from half_orm.model import register
from half_orm.relation import singleton

@register
class Author(blog.get_relation_class('blog.author')):
    Fkeys = {
        'posts_rfk': '_reverse_fkey_blog_post_author_id'
    }
    
    @singleton
    def create_post(self, title, content):
        return self.posts_rfk(title=title, content=content).ho_insert()

# Foreign keys now return your custom classes!
post = Post(title='Welcome').ho_get()
author = post.author_fk().ho_get()  # Returns Author instance
author.create_post("New Post", "Content")  # Custom method available
```

### 🔍 **Intuitive Querying**
```python
# The object IS the filter - no .filter() needed
young_people = Person(birth_date=('>', '1990-01-01'))
gmail_users = Person(email=('ilike', '%@gmail.com'))

# Navigate relationships while filtering
alice_posts = Post().author_fk(name=('ilike', 'alice%'))

# Chain operations naturally
recent_posts = (Post(is_published=True)
    .ho_order_by('created_at desc')
    .ho_limit(10))
```

### 🔧 **PostgreSQL Native Features**
```python
# Use views, functions, and procedures
UserStats = blog.get_relation_class('analytics.user_stats')  # Database view
results = blog.execute_function('calculate_metrics', user_id=123)

# Advanced PostgreSQL data types work seamlessly
JsonData = blog.get_relation_class('app.json_table')
data = JsonData(metadata='{"type": "user", "premium": true}')  # JSONB support
```

## Quick Start

Get up and running in under 5 minutes:

1. **Install halfORM**
   ```bash
   pip install half_orm
   ```

2. **Configure connection**
   ```bash
   mkdir ~/.half_orm
   echo "[database]
   name = my_database
   user = username
   password = password
   host = localhost" > ~/.half_orm/my_database
   ```

3. **Start coding**
   ```python
   from half_orm.model import Model
   
   db = Model('my_database')
   Person = db.get_relation_class('public.person')
   
   # Create
   person = Person(name='Alice', email='alice@example.com')
   result = person.ho_insert()
   
   # Query
   for person in Person(email=('ilike', '%@gmail.com')).ho_select():
       print(f"Found: {person['name']}")
   ```

**[👉 Full Quick Start Guide →](quick-start.md)**

## Documentation Sections

<div class="grid cards" markdown>

-   🚀 **Quick Start**

    ---

    Get up and running with halfORM in minutes. Connect to your database and start working with your data immediately.

    **[Get Started →](quick-start.md)**

-   📚 **Tutorial**

    ---

    Step-by-step guide covering all halfORM concepts from basic CRUD operations to advanced relationship navigation.

    **[Learn halfORM →](tutorial/index.md)**

-   📋 **API Reference**

    ---

    Complete documentation of all halfORM classes, methods, and functions with detailed examples.

    **[API Docs →](api/index.md)**

-   💡 **Examples**

    ---

    Real-world examples and patterns for common use cases like web applications, data analysis, and more.

    **[View Examples →](examples/index.md)**

-   📖 **Guides**

    ---

    In-depth guides on configuration, performance optimization, testing, and migrating from other ORMs.

    **[Browse Guides →](guides/index.md)**

-   🏗️ **Architecture**

    ---

    Understanding halfORM's internals, design principles, and how it works under the hood.

    **[Deep Dive →](architecture/index.md)**

</div>

## Why Choose halfORM?

### ✅ Perfect For

- **PostgreSQL-centric applications** - Leverage PostgreSQL's full power
- **Existing database projects** - Work with established schemas
- **SQL-comfortable teams** - Keep complex logic in the database
- **Rapid prototyping** - Get started instantly
- **Microservices** - Lightweight with no framework baggage

### 🤔 Consider Alternatives If

- **Multi-database support needed** - halfORM is PostgreSQL-only
- **Django ecosystem** - Django ORM may integrate better
- **Code-first approach preferred** - You want to define models in Python
- **Heavy ORM features required** - Need lazy loading, identity maps, etc.

## Community & Support

- **[GitHub Repository](https://github.com/collorg/halfORM)** - Source code and issue tracking
- **[Discussions](https://github.com/collorg/halfORM/discussions)** - Community Q&A and ideas
- **[PyPI Package](https://pypi.org/project/half-orm/)** - Official releases

## What's New

### Version 0.15.0 🎉

!!! success "Latest Release - January 2025"
    Major update with new custom relation classes and breaking changes.

- **🎨 New `@register` decorator** for custom relation classes with business logic
- **🔗 Enhanced foreign key navigation** with custom class resolution  
- **📚 Complete documentation rewrite** with improved structure
- **⚠️ Breaking change**: HOP packager moved to separate `halfORM_dev` package

```python
# New in 0.15.0: Custom relation classes
@register
class Author(blog.get_relation_class('blog.author')):
    Fkeys = {'posts_rfk': '_reverse_fkey_blog_post_author_id'}
    
    @singleton
    def create_post(self, title, content):
        return self.posts_rfk(title=title, content=content).ho_insert()

# Foreign keys now return your custom classes!
post = Post().ho_get()
author = post.author_fk().ho_get()  # Returns Author instance
author.create_post("Title", "Content")  # Custom method available
```

**[📋 View Full Changelog →](https://github.com/collorg/halfORM/releases/tag/v0.15.0)**

### Migration from 0.14.x

!!! warning "HOP Users - Action Required"
    If you were using the `hop` command, install the new package:
    ```bash
    pip install half_orm_dev
    ```
    
    halfORM 0.15.0 focuses exclusively on ORM functionality.

---

!!! tip "Ready to start?"
    Jump into the [Quick Start Guide](quick-start.md) or explore the [Tutorial](tutorial/index.md) for a comprehensive introduction to halfORM.

**Made with ❤️ for PostgreSQL and Python developers**