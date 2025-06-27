# halfORM

[![PyPI version](https://img.shields.io/pypi/v/half_orm)](https://pypi.org/project/half-orm/)
[![Python versions](https://img.shields.io/badge/Python-%20≥%203.7-blue)](https://www.python.org)
[![PostgreSQL versions](https://img.shields.io/badge/PostgreSQL-%20≥%209.6-blue)](https://www.postgresql.org)
[![License](https://img.shields.io/pypi/l/half_orm?color=green)](https://pypi.org/project/half-orm/)
[![Tests](https://github.com/collorg/halfORM/actions/workflows/python-package.yml/badge.svg)](https://github.com/collorg/halfORM/actions/workflows/python-package.yml)
[![Coverage](https://coveralls.io/repos/github/collorg/halfORM/badge.svg?branch=main)](https://coveralls.io/github/collorg/halfORM?branch=main)
[![Downloads](https://static.pepy.tech/badge/half_orm)](https://pepy.tech/project/half_orm)

**The PostgreSQL-native ORM that stays out of your way**

> halfORM lets you keep your database schema in SQL where it belongs, while giving you the comfort of Python for data manipulation. No migrations, no schema conflicts, no ORM fighting — just PostgreSQL and Python working together.

```python
from half_orm.model import Model

# Connect to your existing database
blog = Model('blog_db')

# Work with your existing tables instantly
Post = blog.get_relation_class('blog.post')
Author = blog.get_relation_class('blog.author')

# Clean, intuitive operations
post = Post(title='Hello halfORM!', content='Simple and powerful.')
result = post.ho_insert()
print(f"Created post #{result['id']}")
```

## 🎯 Why halfORM?

**Database-First Approach**: Your PostgreSQL schema is the source of truth. halfORM adapts to your database, not the other way around.

**SQL Transparency**: See exactly what queries are generated with `ho_mogrify()`. No mysterious SQL, no query surprises.

**PostgreSQL Native**: Use views, triggers, stored procedures, and advanced PostgreSQL features without compromise.

## ⚡ Quick Start

### Installation
```bash
pip install half_orm
```

### Configuration (one-time setup)
```bash
# Create config directory
mkdir ~/.half_orm
export HALFORM_CONF_DIR=~/.half_orm

# Create connection file: ~/.half_orm/my_database
echo "[database]
name = my_database
user = username
password = password
host = localhost
port = 5432" > ~/.half_orm/my_database
```

### First Steps
```python
from half_orm.model import Model

# Connect to your database
db = Model('my_database')

# See all your tables and views
print(db)

# Create a class for any table
Person = db.get_relation_class('public.person')

# See the table structure
print(Person())
```

## 🚀 Core Operations

### CRUD Made Simple

```python
# Create
person = Person(first_name='Alice', last_name='Smith', email='alice@example.com')
result = person.ho_insert()

# Read
for person in Person(last_name='Smith').ho_select():
    print(f"{person['first_name']} {person['last_name']}")

# Update
Person(email='alice@example.com').ho_update(last_name='Johnson')

# Delete  
Person(email='alice@example.com').ho_delete()
```

### Smart Querying

```python
# No .filter() method needed - the object IS the filter
young_people = Person(birth_date=('>', '1990-01-01'))
gmail_users = Person(email=('ilike', '%@gmail.com'))

# Navigate and constrain in one step
alice_posts = Post().author_fk(name=('ilike', 'alice%'))

# Chainable operations
recent_posts = (Post(is_published=True)
    .ho_order_by('created_at desc')
    .ho_limit(10)
    .ho_offset(20))

# Set operations
active_or_recent = active_users | recent_users
power_users = premium_users & active_users
```

## 🎨 Custom Relation Classes with Foreign Key Navigation

Override generic relation classes with custom implementations containing business logic and personalized foreign key mappings:

```python
from half_orm.model import Model, register
from half_orm.relation import singleton

blog = Model('blog_db')

@register
class Author(blog.get_relation_class('blog.author')):
    Fkeys = {
        'posts_rfk': '_reverse_fkey_blog_post_author_id',
        'comments_rfk': '_reverse_fkey_blog_comment_author_id',
    }
    
    @singleton
    def create_post(self, title, content):
        """Create a new blog post for this author."""
        return self.posts_rfk(title=title, content=content).ho_insert()
    
    @singleton
    def get_author_s_recent_posts(self, limit=10):
        """Get author's most recent posts."""
        return self.posts_rfk().ho_order_by('published_at desc').ho_limit(limit).ho_select()

    def get_recent_posts(self, limit=10):
        """Get most recent posts."""
        return self.posts_rfk().ho_order_by('published_at desc').ho_limit(limit).ho_select()

@register  
class Post(blog.get_relation_class('blog.post')):
    Fkeys = {
        'author_fk': 'author_id',
        'comments_rfk': '_reverse_fkey_blog_comment_post_id',
    }

    def publish(self):
        """Publish this post."""
        from datetime import datetime
        self.published_at.value = datetime.now()
        return self.ho_update()

# This returns your custom Author class with all methods!
post = Post(title='Welcome').ho_get()
author = post.author_fk().ho_get()  # Instance of your custom Author class

# Use your custom methods
author.create_post("New Post", "Content here")
recent_posts = author.get_recent_posts(5)

# Chain relationships seamlessly  
author.posts_rfk().comments_rfk().author_fk()  # The authors that commented any post of the author
```

## 🔧 Advanced Features

### Transactions
```python
from half_orm.relation import transaction

class Author(db.get_relation_class('blog.author')):
    @transaction
    def create_with_posts(self, posts_data):
        # Everything in one transaction
        author_result = self.ho_insert()
        for post_data in posts_data:
            Post(author_id=author_result['id'], **post_data).ho_insert()
        return author_result
```

### PostgreSQL Functions & Procedures
```python
# Execute functions
results = db.execute_function('my_schema.calculate_stats', user_id=123)

# Call procedures  
db.call_procedure('my_schema.cleanup_old_data', days=30)
```

### Query Debugging
```python
# See the exact SQL being generated
person = Person(last_name=('ilike', 'sm%'))
person.ho_mogrify()
list(person.ho_select())  # or simply list(person)
# Prints: SELECT * FROM person WHERE last_name ILIKE 'sm%'

# Works with all operations
person = Person(email='old@example.com')
person.ho_mogrify()
person.ho_update(email='new@example.com')
# Prints the UPDATE query

# Performance analysis
count = Person().ho_count()
is_empty = Person(email='nonexistent@example.com').ho_is_empty()
```

## 🏗️ Real-World Example

```python
from half_orm.model import Model, register
from half_orm.relation import singleton

# Blog application
blog = Model('blog')

@register
class Author(blog.get_relation_class('blog.author')):
    Fkeys = {
        'posts_rfk': '_reverse_fkey_blog_post_author_id'
    }
    
    @singleton
    def create_post(self, title, content):
        return self.posts_rfk(title=title, content=content).ho_insert()

@register
class Post(blog.get_relation_class('blog.post')):
    Fkeys = {
        'author_fk': 'author_id',
        'comments_rfk': '_reverse_fkey_blog_comment_post_id' 
    }

# Usage
author = Author(name='Jane Doe', email='jane@blog.com')
if author.ho_is_empty():
    author.ho_insert()

# Create post through relationship
post_data = author.create_post(
    title='halfORM is Awesome!',
    content='Here is why you should try it...'
)

post = Post(**post_data)
print(f"Published: {post.title.value}")
print(f"Comments: {post.comments_rfk().ho_count()}")
```

## 📊 halfORM vs. Others

| Feature | SQLAlchemy | Django ORM | Peewee | **halfORM** |
|---------|------------|------------|---------|-------------|
| **Learning Curve** | Steep | Moderate | Gentle | **Minimal** |
| **SQL Control** | Limited | Limited | Good | **Complete** |
| **Custom Business Logic** | Classes/Mixins | Model Methods | Model Methods | **@register decorator** |
| **Database Support** | Multi | Multi | Multi | **PostgreSQL only** |
| **PostgreSQL-Native** | Partial | Partial | No | **✅ Full** |
| **Database-First** | No | No | Partial | **✅ Native** |
| **Setup Complexity** | High | Framework | Low | **Ultra-Low** |
| **Best For** | Complex Apps | Django Web | Multi-DB Apps | **PostgreSQL + Python** |

## 🎓 When to Choose halfORM

### ✅ Perfect For
- **PostgreSQL-centric applications** - You want to leverage PostgreSQL's full power
- **Existing database projects** - You have a schema and want Python access
- **SQL-comfortable teams** - You prefer SQL for complex queries and logic
- **Rapid prototyping** - Get started in seconds, not hours
- **Microservices** - Lightweight, focused ORM without framework baggage

### ⚠️ Consider Alternatives If
- **Multi-database support needed** - halfORM is PostgreSQL-only
- **Django ecosystem** - Django ORM integrates better with Django
- **Team prefers code-first** - You want to define models in Python
- **Heavy ORM features needed** - You need advanced ORM patterns like lazy loading, identity maps, etc.

## 📚 Documentation & Resources

- **[Quick Start Guide](docs/quick-start.md)** - Get running in 5 minutes
- **[Tutorial](docs/tutorial/)** - Step-by-step learning path  
- **[API Reference](docs/api/)** - Complete method documentation
- **[Examples](docs/examples/)** - Real-world applications
- **[Migration Guides](docs/migration/)** - From SQLAlchemy, Django ORM, etc.

## 🤝 Contributing

We welcome contributions! halfORM is designed to stay simple and focused.

- **[Issues](https://github.com/collorg/halfORM/issues)** - Bug reports and feature requests
- **[Discussions](https://github.com/collorg/halfORM/discussions)** - Questions and community
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute code

## 📈 Status & Roadmap

halfORM is actively maintained and used in production. Current focus:

- ✅ **Stable API** - Core features are stable since v0.8
- 🔄 **Performance optimizations** - Query generation improvements  
- 📝 **Documentation expansion** - More examples and guides
- 🧪 **Advanced PostgreSQL features** - Better support for newer PostgreSQL versions

## 📜 License

halfORM is licensed under the [LGPL-3.0](LICENSE) license.

---

> **"Database-first development shouldn't be this hard. halfORM makes it simple."**

**Made with ❤️ for PostgreSQL and Python developers**