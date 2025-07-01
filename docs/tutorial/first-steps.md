# Chapter 2: First Steps

Welcome to your first real halfORM experience! In this chapter, you'll create a complete tutorial database, connect to it with halfORM, and perform your first operations. By the end, you'll understand halfORM's core concepts and be ready for more advanced topics.

## Tutorial Database Setup

Let's start by creating a proper database with realistic data. We'll build a blog application schema that includes authors, posts, comments, and tags - perfect for exploring relationships and real-world patterns.

### Step 1: Create the Tutorial Database

First, let's create the database and user:

```sql title="setup_tutorial_db.sql"
-- Create database and user
-- Run as PostgreSQL superuser: psql -U postgres -f setup_tutorial_db.sql

-- Create tutorial user
CREATE USER tutorial_user WITH PASSWORD 'tutorial_pass';

-- Create tutorial database
CREATE DATABASE blog_tutorial OWNER tutorial_user;
```

```sql title="setup_tutorial_schema.sql"  
-- Run this after connecting to blog_tutorial database
-- psql -U postgres -d blog_tutorial -f setup_tutorial_schema.sql

-- Grant necessary privileges
GRANT ALL PRIVILEGES ON DATABASE blog_tutorial TO tutorial_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO tutorial_user;

-- Create blog schema
CREATE SCHEMA blog AUTHORIZATION tutorial_user;

-- Create tables
CREATE TABLE blog.author (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    bio TEXT,
    birth_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Add table and column comments
COMMENT ON TABLE blog.author IS 'Authors who write blog posts and comments';
COMMENT ON COLUMN blog.author.id IS 'Unique identifier for each author';
COMMENT ON COLUMN blog.author.first_name IS 'Author''s first name';
COMMENT ON COLUMN blog.author.last_name IS 'Author''s last name';
COMMENT ON COLUMN blog.author.email IS 'Author''s email address (must be unique)';
COMMENT ON COLUMN blog.author.bio IS 'Short biography of the author';
COMMENT ON COLUMN blog.author.birth_date IS 'Author''s date of birth';
COMMENT ON COLUMN blog.author.is_active IS 'Whether the author account is active';

CREATE TABLE blog.post (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    content TEXT,
    excerpt TEXT,
    author_id INTEGER NOT NULL REFERENCES blog.author(id) ON DELETE CASCADE,
    published_at TIMESTAMP,
    is_published BOOLEAN DEFAULT FALSE,
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE blog.post IS 'Blog posts with content and metadata';
COMMENT ON COLUMN blog.post.id IS 'Unique identifier for each post';
COMMENT ON COLUMN blog.post.title IS 'Post title displayed to readers';
COMMENT ON COLUMN blog.post.slug IS 'URL-friendly version of the title';
COMMENT ON COLUMN blog.post.content IS 'Full content of the blog post';
COMMENT ON COLUMN blog.post.excerpt IS 'Short summary or preview of the post';
COMMENT ON COLUMN blog.post.author_id IS 'Reference to the author who wrote this post';
COMMENT ON COLUMN blog.post.published_at IS 'When the post was published (NULL for drafts)';
COMMENT ON COLUMN blog.post.is_published IS 'Whether the post is visible to readers';
COMMENT ON COLUMN blog.post.view_count IS 'Number of times this post has been viewed';

CREATE TABLE blog.comment (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    author_id INTEGER NOT NULL REFERENCES blog.author(id) ON DELETE CASCADE,
    post_id INTEGER NOT NULL REFERENCES blog.post(id) ON DELETE CASCADE,
    is_approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE blog.comment IS 'Comments left by readers on blog posts';
COMMENT ON COLUMN blog.comment.id IS 'Unique identifier for each comment';
COMMENT ON COLUMN blog.comment.content IS 'The text content of the comment';
COMMENT ON COLUMN blog.comment.author_id IS 'Reference to the author who wrote this comment';
COMMENT ON COLUMN blog.comment.post_id IS 'Reference to the post this comment belongs to';
COMMENT ON COLUMN blog.comment.is_approved IS 'Whether the comment has been approved for display';

CREATE TABLE blog.tag (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE blog.tag IS 'Tags for categorizing and organizing blog posts';
COMMENT ON COLUMN blog.tag.id IS 'Unique identifier for each tag';
COMMENT ON COLUMN blog.tag.name IS 'Tag name (must be unique)';
COMMENT ON COLUMN blog.tag.description IS 'Optional description of what this tag represents';

CREATE TABLE blog.post_tag (
    post_id INTEGER REFERENCES blog.post(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES blog.tag(id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, tag_id)
);

COMMENT ON TABLE blog.post_tag IS 'Many-to-many relationship linking posts with their tags';

-- Create indexes for performance
CREATE INDEX idx_author_email ON blog.author(email);
CREATE INDEX idx_author_active ON blog.author(is_active);
CREATE INDEX idx_post_author ON blog.post(author_id);
CREATE INDEX idx_post_published ON blog.post(is_published);
CREATE INDEX idx_post_published_at ON blog.post(published_at);
CREATE INDEX idx_post_slug ON blog.post(slug);
CREATE INDEX idx_comment_post ON blog.comment(post_id);
CREATE INDEX idx_comment_author ON blog.comment(author_id);
CREATE INDEX idx_comment_approved ON blog.comment(is_approved);

-- Create useful views
CREATE VIEW blog.published_posts AS
SELECT 
    p.*,
    a.first_name || ' ' || a.last_name AS author_name,
    a.email AS author_email
FROM blog.post p
JOIN blog.author a ON p.author_id = a.id
WHERE p.is_published = TRUE
ORDER BY p.published_at DESC;

COMMENT ON VIEW blog.published_posts IS 'Published posts with author information for public display';

CREATE VIEW blog.post_stats AS
SELECT 
    p.id,
    p.title,
    p.view_count,
    COUNT(c.id) AS comment_count,
    COUNT(CASE WHEN c.is_approved THEN 1 END) AS approved_comment_count
FROM blog.post p
LEFT JOIN blog.comment c ON p.id = c.post_id
GROUP BY p.id, p.title, p.view_count;

COMMENT ON VIEW blog.post_stats IS 'Post statistics including view and comment counts';

-- Grant permissions on new schema
GRANT ALL PRIVILEGES ON SCHEMA blog TO tutorial_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA blog TO tutorial_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA blog TO tutorial_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA blog TO tutorial_user;

-- Insert sample data
INSERT INTO blog.author (first_name, last_name, email, bio, birth_date) VALUES
('Alice', 'Johnson', 'alice@collorg.org', 'Tech writer passionate about Python and databases.', '1985-03-15'),
('Bob', 'Smith', 'bob@collorg.org', 'Full-stack developer and PostgreSQL enthusiast.', '1990-07-22'),
('Carol', 'Brown', 'carol@collorg.org', 'Data scientist with a love for clear explanations.', '1988-11-08'),
('David', 'Wilson', 'david@collorg.org', 'DevOps engineer and automation expert.', '1992-01-30');

INSERT INTO blog.tag (name, description) VALUES
('python', 'Python programming language'),
('postgresql', 'PostgreSQL database'),
('orm', 'Object-Relational Mapping'),
('tutorial', 'Educational content'),
('performance', 'Performance optimization'),
('best-practices', 'Best practices and patterns');

INSERT INTO blog.post (title, slug, content, excerpt, author_id, published_at, is_published, view_count) VALUES
(
    'Getting Started with halfORM',
    'getting-started-halfORM',
    'halfORM is a PostgreSQL-native ORM that takes a database-first approach...',
    'Learn the basics of halfORM and why it''s different from other ORMs.',
    1,
    NOW() - INTERVAL '7 days',
    TRUE,
    245
),
(
    'Advanced PostgreSQL Features',
    'advanced-postgresql-features',
    'PostgreSQL offers many advanced features that most ORMs don''t support well...',
    'Explore PostgreSQL''s advanced features and how to use them with halfORM.',
    2,
    NOW() - INTERVAL '3 days',
    TRUE,
    189
),
(
    'Database Performance Tips',
    'database-performance-tips',
    'Optimizing database performance requires understanding both your queries and your data...',
    'Practical tips for improving database performance in production applications.',
    3,
    NOW() - INTERVAL '1 day',
    TRUE,
    156
),
(
    'Working with Relationships',
    'working-with-relationships',
    'Foreign keys and relationships are at the heart of relational databases...',
    'Master foreign key navigation and relationship patterns in halfORM.',
    1,
    NULL,
    FALSE,
    0
);

-- Link posts with tags
INSERT INTO blog.post_tag (post_id, tag_id) VALUES
(1, 3), (1, 4),  -- halfORM post: orm, tutorial
(2, 2), (2, 5),  -- PostgreSQL post: postgresql, performance  
(3, 2), (3, 5), (3, 6),  -- Performance post: postgresql, performance, best-practices
(4, 3), (4, 4);  -- Relationships post: orm, tutorial

INSERT INTO blog.comment (content, author_id, post_id, is_approved) VALUES
('Great introduction! This really helped me understand the differences.', 2, 1, TRUE),
('Thanks for the clear explanations. Looking forward to more posts!', 3, 1, TRUE),
('Could you cover transactions in a future post?', 4, 1, TRUE),
('Excellent deep dive into PostgreSQL features. Very practical!', 1, 2, TRUE),
('The performance tips section was especially helpful.', 4, 2, TRUE),
('This saved me hours of debugging. Thank you!', 2, 3, TRUE),
('Would love to see examples with larger datasets.', 1, 3, FALSE);
```

### Step 2: Run the Setup Scripts

Execute the scripts to create your tutorial database:

```bash
# Create the database and user
psql -U postgres -f setup_tutorial_db.sql

# Connect to the new database and create the schema
psql -U postgres -d blog_tutorial -f setup_tutorial_schema.sql

# Verify the setup
psql -U tutorial_user -d blog_tutorial -c "\dt blog.*"
```

Expected output:
```
           List of relations
 Schema |   Name   | Type  |     Owner
--------+----------+-------+---------------
 blog   | author   | table | tutorial_user
 blog   | comment  | table | tutorial_user
 blog   | post     | table | tutorial_user
 blog   | post_tag | table | tutorial_user
 blog   | tag      | table | tutorial_user
```

### Step 3: Configure halfORM Connection

Create a configuration file for the tutorial database:

```bash
# Create config directory if it doesn't exist
mkdir -p ~/.half_orm
export HALFORM_CONF_DIR=~/.half_orm
```

```ini title="~/.half_orm/blog_tutorial"
[database]
name = blog_tutorial
user = tutorial_user
password = tutorial_pass
host = localhost
port = 5432
```

### Step 4: Test the Setup

```bash
# Test the new database connection
python -m half_orm
```

You should see something like:
```
[halfORM] version 0.15.0
✅ Connected to template1 database (default setup)

== Checking connections for files in HALFORM_CONF_DIR=/home/user/.half_orm
✅ blog_tutorial
```

Perfect! Now you have a working tutorial database with sample data.

## Connecting to Your Database

Let's start exploring halfORM by connecting to our new database:

```python title="first_connection.py"
#!/usr/bin/env python3
"""
First connection to the tutorial database
"""

# Import halfORM
from half_orm.model import Model

# Connect to the tutorial database
blog = Model('blog_tutorial')

print("🎉 Connected to blog_tutorial database!")
print(blog)
```

### Understanding the Model Class

The `Model` class is your entry point to halfORM. It represents a connection to a specific PostgreSQL database and provides methods to:

- **Get relation classes** for tables and views
- **Execute raw SQL** when needed
- **Manage transactions** 
- **Access database metadata**

## Exploring the Database Schema

Let's explore what's in our database using halfORM:

```python title="explore_database.py"
#!/usr/bin/env python3
"""
Explore the tutorial database structure
"""

from half_orm.model import Model

blog = Model('blog_tutorial')

# halfORM automatically discovers all relations (tables and views)
print(blog)
```

Expected output:
```
📋 Available relations for blog_tutorial:
r "blog"."author"           → Authors who write blog posts and comments
r "blog"."comment"          → Comments left by readers on blog posts
r "blog"."post"             → Blog posts with content and metadata
r "blog"."post_tag"         → Many-to-many relationship linking posts with their tags
r "blog"."tag"              → Tags for categorizing and organizing blog posts
v "blog"."post_stats"       → Post statistics including view and comment counts
v "blog"."published_posts"  → Published posts with author information for public display

📋 Relation Types:
  r: Table
  p: Partioned table
  v: View
  m: Materialized view
  f: Foreign data
```

## Creating Your First Relation Class

In halfORM, you work with **relation classes** that represent tables or views. Let's create our first one:

```python title="first_relation_class.py"
#!/usr/bin/env python3
"""
Working with relation classes
"""

from half_orm.model import Model

blog = Model('blog_tutorial')

# Create a relation class for the author table
Author = blog.get_relation_class('blog.author')

print("✅ Created Author relation class")
print(f"📝 Class: {Author}")
print(f"🎯 Represents: blog.author table")

# Explore the table structure
print("\n🔍 Table structure:")
print(Author())
```

When you run this, you'll see detailed information about the `blog.author` table:

```
DATABASE: blog_tutorial
SCHEMA: blog
TABLE: author
DESCRIPTION:
Authors who write blog posts and comments
FIELDS:
- id:         (int4) NOT NULL
- first_name: (varchar) NOT NULL
- last_name:  (varchar) NOT NULL
- email:      (varchar) NOT NULL
- bio:        (text)
- birth_date: (date)
- is_active:  (bool)
- created_at: (timestamp)
- updated_at: (timestamp)
PRIMARY KEY (id)
UNIQUE CONSTRAINT (email)
FOREIGN KEYS:
- *reverse*fkey_blog_tutorial_blog_comment_author_id: ("id")
 ↳ "blog_tutorial":"blog"."comment"(author_id)
- *reverse*fkey_blog_tutorial_blog_post_author_id: ("id")
 ↳ "blog_tutorial":"blog"."post"(author_id)
To use the foreign keys as direct attributes of the class, copy/paste the Fkeys below into
your code as a class attribute and replace the empty string key(s) with the alias(es) you
want to use. The aliases must be unique and different from any of the column names. Empty
string keys are ignored.
Fkeys = {
    '': '_reverse_fkey_blog_tutorial_blog_comment_author_id',
    '': '_reverse_fkey_blog_tutorial_blog_post_author_id',
}
```

!!! tip "Understanding the Output"
    halfORM shows you:
    
    - **Database, schema, and table information** with PostgreSQL comments
    - **Field details** with types and constraints (NOT NULL, etc.)
    - **Primary keys and unique constraints** clearly marked
    - **Foreign key relationships** including reverse foreign keys (incoming references)
    - **Ready-to-use Fkeys template** that you can copy/paste into your custom classes
    - **Clear instructions** on how to use foreign keys as class attributes

!!! important "Schema Names Are Required"
    halfORM always requires the full `schema.table` format in `get_relation_class()`:
    
    ```sql
    -- When you create a table without specifying a schema
    CREATE TABLE users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) NOT NULL
    );
    -- PostgreSQL automatically places it in the 'public' schema
    ```
    
    ```python
    # ✅ Correct - always include schema name
    Author = blog.get_relation_class('blog.author')
    Product = blog.get_relation_class('inventory.products')
    User = blog.get_relation_class('public.users')  # Even for public schema
    
    # ❌ Wrong - will raise MissingSchemaInName error
    Author = blog.get_relation_class('author')
    User = blog.get_relation_class('users')
    ```
    
    Even though PostgreSQL creates the table in the `public` schema by default, halfORM requires you to be explicit: use `public.users` to access it.

## Your First CRUD Operations

Now let's perform basic Create, Read, Update, Delete operations:

### Reading Data (R)

```python title="read_operations.py"
#!/usr/bin/env python3
"""
Reading data with halfORM
"""

from half_orm.model import Model

blog = Model('blog_tutorial')
Author = blog.get_relation_class('blog.author')

print("📖 Reading data from the database")
print("=" * 40)

# Method 1: Simple iteration - objects are iterators!
print("\n👥 All authors (using iteration):")
for author in Author():
    print(f"  📝 {author['first_name']} {author['last_name']} ({author['email']})")

# Method 2: Explicit ho_select() for all columns (equivalent to above)
print("\n👥 All authors (using ho_select):")
all_authors = Author().ho_select()
for author in all_authors:
    print(f"  📝 {author['first_name']} {author['last_name']} ({author['email']})")

# Method 3: ho_select() with specific columns (this is where it's really needed)
print("\n📧 Just names and emails (ho_select with column selection):")
author_info = Author().ho_select('first_name', 'last_name', 'email')
for author in author_info:
    print(f"  👤 {author['first_name']} {author['last_name']} - {author['email']}")

# Method 4: Count records
author_count = Author().ho_count()
print(f"\n🔢 Total authors: {author_count}")

# Method 5: Get one specific author
alice = Author(email='alice@collorg.org').ho_get()
print(f"\n🎯 Found Alice: {alice.first_name} {alice.last_name}")
```

### Creating Data (C)

```python title="create_operations.py"
#!/usr/bin/env python3
"""
Creating new data with halfORM
"""

from half_orm.model import Model

blog = Model('blog_tutorial')
Author = blog.get_relation_class('blog.author')

print("➕ Creating new data")
print("=" * 30)

# Create a new author
new_author = Author(
    first_name='Emma',
    last_name='Wilson',
    email='emma@collorg.org',
    bio='Frontend developer passionate about user experience.',
    birth_date='1991-05-12'
)

# Check if author already exists
if Author(email=new_author.email).ho_is_empty():
    # Insert the new author
    result = new_author.ho_insert()
    print(f"✅ Created new author: {result}")
    print(f"📝 New author ID: {result['id']}")
else:
    print("ℹ️  Author already exists")

# Verify the creation
emma = Author(email='emma@collorg.org').ho_get()
print(f"🎉 Verified: {emma.first_name} {emma.last_name} is in the database")
```

### Updating Data (U)

```python title="update_operations.py"
#!/usr/bin/env python3
"""
Updating data with halfORM
"""

from half_orm.model import Model

blog = Model('blog_tutorial')
Author = blog.get_relation_class('blog.author')

print("📝 Updating data")
print("=" * 25)

# Find Emma and update her bio
emma = Author(email='emma@collorg.org')

if not emma.ho_is_empty():
    # Update the bio
    result = emma.ho_update(
        bio='Frontend developer and UX designer passionate about accessible web applications.'
    )
    print(f"✅ Updated Emma's bio")
    
    # Verify the update
    updated_emma = Author(email='emma@collorg.org').ho_get()
    print(f"📝 New bio: {updated_emma.bio}")
else:
    print("❌ Emma not found in database")
```

### Deleting Data (D)

```python title="delete_operations.py"
#!/usr/bin/env python3
"""
Deleting data with halfORM
"""

from half_orm.model import Model

blog = Model('blog_tutorial')
Author = blog.get_relation_class('blog.author')

print("🗑️  Deleting data")
print("=" * 25)

# Find Emma
emma = Author(email='emma@collorg.org')

if not emma.ho_is_empty():
    # Delete Emma
    emma.ho_delete()
    print("✅ Deleted Emma from database")
    
    # Verify deletion
    check_emma = Author(email='emma@collorg.org')
    if check_emma.ho_is_empty():
        print("✅ Confirmed: Emma is no longer in database")
else:
    print("ℹ️  Emma not found in database")
```

## Basic Filtering and Querying

halfORM's filtering approach is unique - the object IS the filter. To define a subset, you need to specify constraints on the values of the fields/columns:

- **Single value** for an exact match: `Author(name='John')`
- **Tuple `(comp, value)`** for other comparisons, where `comp` is either a SQL
[comparison operator](https://www.postgresql.org/docs/current/static/functions-comparison.html) or a [pattern matching operator (like or POSIX regular expression)](https://www.postgresql.org/docs/current/static/functions-matching.html): `Author(email=('like', '%@collorg.org'))`

```python title="filtering_examples.py"
#!/usr/bin/env python3
"""
Filtering and querying examples
"""

from half_orm.model import Model

blog = Model('blog_tutorial')
Author = blog.get_relation_class('blog.author')
Post = blog.get_relation_class('blog.post')

print("🔍 Filtering and querying")
print("=" * 35)

# Example 1: Exact match (single value)
print("\n📧 Author with specific email:")
alice = Author(email='alice@collorg.org').ho_get()
print(f"  📝 {alice.first_name} {alice.last_name}")

# Example 2: Pattern matching with ILIKE
print("\n📧 Authors with collorg.org addresses:")
collorg_authors = Author(email=('ilike', '%@collorg.org'))
for author in collorg_authors:
    print(f"  📮 {author['first_name']} {author['last_name']}")

# Example 3: Boolean filter (exact match)
print("\n✅ Active authors:")
active_authors = Author(is_active=True).ho_select('first_name', 'last_name')
for author in active_authors:
    print(f"  👤 {author['first_name']} {author['last_name']}")

# Example 4: Date comparison (tuple form)
print("\n📅 Authors born after 1988:")
young_authors = Author(birth_date=('>', '1988-01-01')).ho_select('first_name', 'last_name', 'birth_date')
for author in young_authors:
    print(f"  🎂 {author['first_name']} {author['last_name']} ({author['birth_date']})")

# Example 5: Published posts (exact match)
print("\n📰 Published posts:")
published_posts = Post(is_published=True).ho_select('title', 'view_count')
for post in published_posts:
    print(f"  📄 {post['title']} ({post['view_count']} views)")

# Example 6: Ordering and limiting
print("\n🔥 Most viewed posts:")
popular_posts = (Post(is_published=True)
    .ho_order_by('view_count desc')
    .ho_limit(3)
    .ho_select('title', 'view_count'))

for post in popular_posts:
    print(f"  🌟 {post['title']} - {post['view_count']} views")
```

## Understanding halfORM Concepts

### Key Concepts You've Learned

1. **Model Class** - Your database connection and entry point
2. **Relation Classes** - Represent tables/views (created with `get_relation_class()`)
3. **Object-as-Filter** - Create instances with filter criteria
4. **ho_methods** - All halfORM operations start with `ho_`
5. **Chain Operations** - Order, limit, offset operations can be chained

### Method Patterns

| Pattern | Purpose | Example |
|---------|---------|---------|
| `for x in relation:` | Iterate all records | `for author in Author(): print(author['name'])` |
| `ho_select()` | All columns explicitly | `Author().ho_select()` (same as iteration) |
| `ho_select('col1', 'col2')` | Specific columns | `Author().ho_select('name', 'email')` |
| `ho_get()` | Get single record. Returns a Relation object | `Author(id=1).ho_get()` |
| `ho_insert()` | Create new record | `Author(name='John').ho_insert()` |
| `ho_update()` | Modify existing | `Author(id=1).ho_update(name='Jane')` |
| `ho_delete()` | Remove records | `Author(id=1).ho_delete()` |
| `ho_count()` | Count records | `Author().ho_count()` |
| `ho_is_empty()` | Check existence | `Author(email='test').ho_is_empty()` |

### Filtering Operators

halfORM supports two forms of constraints:

| Form | Usage | Example | SQL Generated |
|------|-------|---------|---------------|
| **Single value** | Exact match | `Author(name='John')` | `WHERE name = 'John'` |
| **Tuple (comp, value)** | Custom comparison | `Author(age=('>', 18))` | `WHERE age > 18` |

#### Common Comparison Operators

| Operator | SQL Equivalent | Example | Description |
|----------|----------------|---------|-------------|
| `=` (default) | `=` | `Author(name='John')` | Exact equality |
| `('>', value)` | `>` | `Author(age=('>', 18))` | Greater than |
| `('<', value)` | `<` | `Author(age=('<', 65))` | Less than |
| `('>=', value)` | `>=` | `Author(age=('>=', 21))` | Greater than or equal |
| `('<=', value)` | `<=` | `Author(age=('<=', 65))` | Less than or equal |
| `('!=', value)` | `!=` | `Author(status=('!=', 'inactive'))` | Not equal |

#### Pattern Matching Operators

| Operator | SQL Equivalent | Example | Description |
|----------|----------------|---------|-------------|
| `('like', pattern)` | `LIKE` | `Author(name=('like', 'John%'))` | Case-sensitive pattern |
| `('ilike', pattern)` | `ILIKE` | `Author(email=('ilike', '%@gmail.com'))` | Case-insensitive pattern |
| `('~', pattern)` | `~` | `Author(name=('~', '^[A-Z]'))` | POSIX regex (case-sensitive) |
| `('~*', pattern)` | `~*` | `Author(name=('~*', '^john'))` | POSIX regex (case-insensitive) |

#### List and Range Operators

| Operator | SQL Equivalent | Example | Description |
|----------|----------------|---------|-------------|
| `('in', list)` | `IN` | `Author(id=('in', [1, 2, 3]))` | Value in list |
| `('not in', list)` | `NOT IN` | `Author(status=('not in', ['deleted', 'banned']))` | Value not in list |
| `('between', (a, b))` | `BETWEEN` | `Author(age=('between', (18, 65)))` | Value between range |

## SQL Transparency - See What's Generated

One of halfORM's key features is SQL transparency. You can see exactly what SQL query is executed:

```python title="sql_transparency.py"
#!/usr/bin/env python3
"""
Seeing the generated SQL
"""

from half_orm.model import Model

blog = Model('blog_tutorial')
Author = blog.get_relation_class('blog.author')

print("🔍 SQL Transparency")
print("=" * 30)

# Create a query
query = Author(is_active=True).ho_order_by('last_name')

# See the SQL without executing
print("\n📝 Generated SQL:")
query.ho_mogrify()

# Now execute and see results
print("\n📊 Results:")
results = query.ho_select('first_name', 'last_name')
for result in results:
    print(f"  👤 {result['first_name']} {result['last_name']}")
```

This will show you the exact SQL being generated, helping you understand what halfORM is doing and optimize your queries.

## What's Next?

Congratulations! You've successfully:

- ✅ Set up a complete tutorial database with realistic data
- ✅ Connected to PostgreSQL using halfORM
- ✅ Created your first relation classes
- ✅ Performed all basic CRUD operations
- ✅ Used halfORM's filtering and querying features
- ✅ Understood key halfORM concepts and patterns

In the next chapter, [Models & Relations](models-relations.md), you'll learn:

- How to create custom relation classes with business logic
- Using the `@register` decorator for enhanced functionality
- Working with more complex data types and constraints
- Best practices for organizing your halfORM code

---

**Ready to go deeper?** Continue to [Chapter 3: Models & Relations](models-relations.md)!

!!! tip "Practice Makes Perfect"
    Try modifying the examples above:
    
    - Create new authors and posts
    - Experiment with different filters
    - Try combining multiple filter conditions
    - Explore the other tables (comment, tag, post_tag)
    
    The best way to learn halfORM is by experimenting with real data!