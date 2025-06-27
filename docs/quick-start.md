# Quick Start Guide

Get up and running with halfORM in under 5 minutes. This guide will take you from installation to your first successful database operation.

!!! tip "Prerequisites"
    - Python 3.7 or higher
    - PostgreSQL 9.6 or higher
    - Basic familiarity with Python and SQL

## Step 1: Installation

Install halfORM using pip:

```bash
pip install half_orm
```

!!! info "Virtual Environment Recommended"
    It's recommended to install halfORM in a virtual environment:
    ```bash
    python -m venv halfORM-env
    source halfORM-env/bin/activate  # Linux/Mac
    # or halfORM-env\Scripts\activate  # Windows
    pip install half_orm
    ```
    
    **Pro tip:** For automatic virtual environment management, check out [auto-venv](https://github.com/collorg/auto_venv) - it handles virtual environments seamlessly!

## Step 2: Database Setup

For this guide, we'll create a simple blog database. If you already have a PostgreSQL database, you can skip to [Step 3](#step-3-configuration).

### Create Example Database

Connect to PostgreSQL and create our example:

```sql
-- Connect to PostgreSQL as superuser
CREATE DATABASE halform_quickstart;

-- Reconnect to the new database (separate command)
\c halform_quickstart

-- Create schema
CREATE SCHEMA blog;

-- Create tables
CREATE TABLE blog.author (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE blog.post (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    author_id INTEGER REFERENCES blog.author(id),
    published_at TIMESTAMP DEFAULT NOW(),
    is_published BOOLEAN DEFAULT FALSE
);

-- Add some sample data
INSERT INTO blog.author (name, email) VALUES 
    ('Alice Johnson', 'alice@example.com'),
    ('Bob Smith', 'bob@example.com');

INSERT INTO blog.post (title, content, author_id, is_published) VALUES 
    ('Welcome to halfORM', 'This is our first post using halfORM!', 1, true),
    ('Database-First Development', 'Why schema-first approach rocks...', 1, true),
    ('Draft Post', 'This is still a work in progress.', 2, false);
```

## Step 3: Configuration

### Create Configuration Directory

```bash
# Create config directory
mkdir ~/.half_orm
export HALFORM_CONF_DIR=~/.half_orm
```

!!! note "Windows Users"
    On Windows, set the environment variable through System Properties:
    1. Right-click "This PC" → Properties
    2. Advanced system settings → Environment Variables
    3. Add `HALFORM_CONF_DIR` with value like `C:\Users\YourName\.half_orm`

### Create Connection File

Create a connection file in your config directory:

```ini title="~/.half_orm/halform_quickstart"
[database]
name = halform_quickstart
user = your_username
password = your_password
host = localhost
port = 5432
```

### Alternative: Trusted Authentication

!!! tip "Skip Configuration (PostgreSQL with trusted auth)"
    Since version 0.14, if no config file exists, halfORM attempts trusted authentication with a role matching `$USER`. 
    
    If your PostgreSQL is configured for trusted authentication (common in development), you can skip the configuration file entirely and go directly to [Step 4](#step-4-first-connection)!
    
    All examples will work with or without the config file:
    ```python
    blog = Model('halform_quickstart')  # Works with or without config file!
    ```

## Step 4: First Connection

Let's verify everything works:

```python title="test_connection.py"
from half_orm.model import Model

try:
    # Connect to the database
    blog = Model('halform_quickstart')
    
    # Show all relations in the database
    print("✅ Connected successfully!")
    print("\nDatabase structure:")
    print(blog)
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("Check your database is running and credentials are correct.")
```

Expected output:
```
✅ Connected successfully!

Database structure:
r "blog"."author"
r "blog"."post"
```

## Step 5: Create Your First Classes

```python title="blog_models.py"
from half_orm.model import Model

# Connect to database
blog = Model('halform_quickstart')

# Create classes for our tables
class Author(blog.get_relation_class('blog.author')):
    """Authors who write blog posts"""
    pass

class Post(blog.get_relation_class('blog.post')):
    """Blog posts with content"""
    pass

# Explore the table structure
if __name__ == "__main__":
    print("=== Author Table ===")
    print(Author())
    
    print("\n=== Post Table ===")  
    print(Post())
```

This will show you the complete table structure, including columns, types, constraints, and foreign keys.

## Step 6: Basic CRUD Operations

Now let's perform some basic operations:

```python title="crud_examples.py"
from half_orm.model import Model

blog = Model('halform_quickstart')

class Author(blog.get_relation_class('blog.author')):
    pass

class Post(blog.get_relation_class('blog.post')):
    pass

# === CREATE ===
print("Creating a new author...")
new_author = Author(
    name='Charlie Brown', 
    email='charlie@example.com'
)

# Check if author already exists
if new_author.ho_is_empty():
    result = new_author.ho_insert()
    print(f"✅ Created author: {result}")
else:
    print("Author already exists!")

# === READ ===
print("\nReading authors...")
for author in Author().ho_select('name', 'email'):
    print(f"📝 {author['name']} ({author['email']})")

# === UPDATE ===
print("\nUpdating author email...")
charlie = Author(name='Charlie Brown')
if not charlie.ho_is_empty():
    charlie.ho_update(email='charlie.brown@newdomain.com')
    print("✅ Email updated!")

# === DELETE ===
print("\nDeleting test author...")
Author(name='Charlie Brown').ho_delete()
print("✅ Author deleted!")
```

## Step 7: Working with Relationships

halfORM makes working with foreign keys intuitive:

```python title="relationships.py"
from half_orm.model import Model

blog = Model('halform_quickstart')

class Author(blog.get_relation_class('blog.author')):
    # Define foreign key relationships
    Fkeys = {
        'posts_rfk': '_reverse_fkey_halform_quickstart_blog_post_author_id'
    }

class Post(blog.get_relation_class('blog.post')):
    Fkeys = {
        'author_fk': 'post_author_id_fkey'
    }

# Find an author
alice = Author(name='Alice Johnson').ho_get()
print(f"Author: {alice.name.value}")

# Get all posts by this author
alice_posts = alice.posts_rfk()
print(f"\nPosts by {alice.name.value}:")
for post in alice_posts.ho_select('title', 'is_published'):
    status = "✅ Published" if post['is_published'] else "📝 Draft"
    print(f"  - {post['title']} ({status})")

# Get author from a post
first_post = Post(title='Welcome to halfORM').ho_get()
post_author = first_post.author_fk().ho_get()
print(f"\n'{first_post.title.value}' was written by: {post_author.name.value}")
```

!!! tip "Foreign Key Names"
    When you print a relation (e.g., `print(Author())`), halfORM shows you the exact foreign key names to use in your `Fkeys` dictionary. Just copy and paste them!

## Step 8: Query Filtering and Chaining

halfORM supports flexible querying:

```python title="querying.py"
from half_orm.model import Model

blog = Model('halform_quickstart')

class Author(blog.get_relation_class('blog.author')):
    Fkeys = {
        'posts_rfk': '_reverse_fkey_halform_quickstart_blog_post_author_id'
    }

class Post(blog.get_relation_class('blog.post')):
    Fkeys = {
        'author_fk': 'post_author_id_fkey'
    }

# === FILTERING ===
# Exact match
published_posts = Post(is_published=True)

# Comparison operators
recent_posts = Post(published_at=('>', '2024-01-01'))

# Pattern matching with foreign key navigation
alice_posts = Post().author_fk(name=('ilike', 'alice%'))

# === CHAINING ===
# Get recent published posts, ordered by date
recent_published = (Post(is_published=True)
    .ho_order_by('published_at DESC')
    .ho_limit(5))

for post in recent_published.ho_select('title', 'published_at'):
    print(f"📖 {post['title']} ({post['published_at']})")

# === COUNTING ===
total_posts = Post().ho_count()
published_count = Post(is_published=True).ho_count()
draft_count = Post(is_published=False).ho_count()

print(f"\n📊 Statistics:")
print(f"Total posts: {total_posts}")
print(f"Published: {published_count}")
print(f"Drafts: {draft_count}")

# === DEBUGGING ===
# See the generated SQL
query = Post(is_published=True).ho_order_by('published_at DESC')
query.ho_mogrify()
list(query.ho_select())  # This will print the SQL query
```

## Step 9: Register Custom Classes (Optional)

For advanced use cases, you can override the auto-generated classes with custom implementations that include business logic and cleaner foreign key mappings:

```python title="custom_blog_classes.py"
from half_orm.model import Model, register

blog = Model('halform_quickstart')

@register
class Author(blog.get_relation_class('blog.author')):
    """Custom Author class with business methods"""
    Fkeys = {
        'posts_rfk': '_reverse_fkey_halform_quickstart_blog_post_author_id'
    }
    
    def create_post(self, title, content, published=False):
        """Create a new post for this author."""
        return self.posts_rfk(
            title=title, 
            content=content, 
            is_published=published
        ).ho_insert()
    
    def get_published_posts(self):
        """Get all published posts by this author."""
        return self.posts_rfk(is_published=True).ho_select()
    
    def get_stats(self):
        """Get author statistics."""
        all_posts = self.posts_rfk()
        published = all_posts(is_published=True)
        return {
            'total_posts': all_posts.ho_count(),
            'published_posts': published.ho_count(),
            'draft_posts': all_posts.ho_count() - published.ho_count()
        }

@register
class Post(blog.get_relation_class('blog.post')):
    """Custom Post class with business methods"""
    Fkeys = {
        'author_fk': 'post_author_id_fkey'
    }
    
    def publish(self):
        """Publish this post."""
        from datetime import datetime
        self.is_published.value = True
        self.published_at.value = datetime.now()
        return self.ho_update()
    
    def unpublish(self):
        """Unpublish this post."""
        self.is_published.value = False
        return self.ho_update()
    
    def get_author_name(self):
        """Get the name of this post's author."""
        return self.author_fk().ho_get().name.value

# Test the custom classes
if __name__ == "__main__":
    # Find Alice
    alice = Author(name='Alice Johnson').ho_get()
    
    # Create a post using custom method
    new_post = alice.create_post(
        title="halfORM Custom Classes", 
        content="This post was created using a custom method!",
        published=True
    )
    print(f"✅ Created post: {new_post}")
    
    # Get author statistics
    stats = alice.get_stats()
    print(f"📊 Alice's stats: {stats}")
    
    # Navigate from post to author using custom method
    post = Post(title='Welcome to halfORM').ho_get()
    author_name = post.get_author_name()
    print(f"📝 '{post.title.value}' was written by: {author_name}")
```

### The Power of @register

Once registered, your custom classes are returned automatically by foreign key relationships:

```python
# Before @register: generic classes with limited functionality
post = Post(title='Welcome').ho_get()
author = post.author_fk().ho_get()  # Generic Author class
# author only has basic CRUD methods

# After @register: your custom classes with business logic
post = Post(title='Welcome').ho_get()  
author = post.author_fk().ho_get()  # YOUR custom Author class!
author.create_post("New Post", "Content")  # Custom methods available!
stats = author.get_stats()  # Your business logic works!
```

### Benefits

- **Clean Fkeys**: Use friendly names instead of long constraint names
- **Business Logic**: Encapsulate domain logic in your relation classes
- **Automatic Resolution**: Foreign keys return your custom classes
- **No Performance Cost**: Registration happens at import time
- **Code Preservation**: Your custom code survives class regeneration

!!! tip "When to Use Custom Classes"
    Use `@register` when you need:
    - Business logic methods on your data objects
    - Cleaner, more readable foreign key names
    - Domain-specific validation or computed properties
    - Complex operations that involve multiple tables
    
    For simple CRUD operations, the auto-generated classes work perfectly!

## Next Steps

Congratulations! You've successfully:

- ✅ Installed and configured halfORM
- ✅ Connected to a PostgreSQL database  
- ✅ Created relation classes
- ✅ Performed CRUD operations
- ✅ Navigated relationships
- ✅ Built filtered queries

### Where to go next:

1. **[Tutorial](tutorial/index.md)** - Deep dive into halfORM concepts
2. **[Foreign Keys Guide](tutorial/foreign-keys.md)** - Master relationship navigation
3. **[Examples](examples/index.md)** - See real-world applications
4. **[API Reference](api/index.md)** - Complete method documentation

### Common next questions:

- **Transactions?** → See [Transactions Tutorial](tutorial/transactions.md)
- **Complex queries?** → Check [Advanced Querying](guides/advanced-queries.md)
- **Performance tips?** → Read [Performance Guide](guides/performance.md)
- **Migration from other ORMs?** → Visit [Migration Guides](guides/migration.md)

## Troubleshooting

### Connection Issues
```python
# Test your connection
from half_orm.model import Model

try:
    db = Model('your_config_name')
    print("✅ Connection successful!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    # Check database is running, credentials are correct
```

### Configuration Problems
```bash
# Verify config file location
echo $HALFORM_CONF_DIR
ls -la $HALFORM_CONF_DIR

# Check config file format
cat $HALFORM_CONF_DIR/your_config_file
```

### Import Errors
```bash
# Verify halfORM installation
pip show half_orm

# Reinstall if needed
pip install --upgrade half_orm
```

!!! question "Need Help?"
    - Check the [FAQ](../faq.md) for common issues
    - Join [GitHub Discussions](https://github.com/collorg/halfORM/discussions) for community help
    - Report bugs via [GitHub Issues](https://github.com/collorg/halfORM/issues)

---

**You're now ready to build amazing PostgreSQL applications with halfORM!** 🚀