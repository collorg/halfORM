# Chapter 2: First Steps

Welcome to your first real halfORM experience! In this chapter, you'll create a complete tutorial database, connect to it with halfORM, and perform your first operations. By the end, you'll understand halfORM's core concepts and be ready for more advanced topics.

!!! important "Core Concepts"
    This chapter introduces halfORM's fundamental concepts in action. For complete reference on these concepts, see **[halfORM Fundamentals](../fundamentals.md)** which covers:
    
    - Object-as-filter pattern and constraint syntax
    - Declarative programming and lazy evaluation
    - Method naming conventions (ho_ prefix)
    - Database-first philosophy
    
    You can read Fundamentals now or refer to it as needed during this chapter.

## Tutorial Database Setup

Let's create a realistic blog database with relationships and sample data.

### Step 1: Create the Tutorial Database

```sh
sudo su - postgresql
psql template1
```

```sql
-- Create database and user
CREATE DATABASE blog_tutorial;
CREATE USER tutorial_user WITH PASSWORD 'tutorial_pass'; -- change the password
GRANT ALL PRIVILEGES ON DATABASE blog_tutorial TO tutorial_user;
```

Save the file `tutorial_setup.sql`.

```sql title="tutorial_setup.sql"
-- Create schema
CREATE SCHEMA blog;

-- Create tables
CREATE TABLE blog.author (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    bio TEXT,
    birth_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE blog.post (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    author_id INTEGER NOT NULL REFERENCES blog.author(id) ON DELETE CASCADE,
    published_at TIMESTAMP,
    is_published BOOLEAN DEFAULT FALSE,
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE blog.comment (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    author_id INTEGER NOT NULL REFERENCES blog.author(id) ON DELETE CASCADE,
    post_id INTEGER NOT NULL REFERENCES blog.post(id) ON DELETE CASCADE,
    is_approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Add sample data
INSERT INTO blog.author (first_name, last_name, email, bio, birth_date) VALUES
('Alice', 'Johnson', 'alice@example.com', 'Tech writer passionate about databases.', '1985-03-15'),
('Bob', 'Smith', 'bob@example.com', 'Full-stack developer and PostgreSQL enthusiast.', '1990-07-22'),
('Carol', 'Brown', 'carol@example.com', 'Data scientist with a love for clear explanations.', '1988-11-08');

INSERT INTO blog.post (title, content, author_id, published_at, is_published, view_count) VALUES
('Getting Started with halfORM', 'halfORM is a PostgreSQL-native ORM...', 1, NOW() - INTERVAL '7 days', TRUE, 245),
('Advanced PostgreSQL Features', 'PostgreSQL offers many advanced features...', 2, NOW() - INTERVAL '3 days', TRUE, 189),
('Database Performance Tips', 'Optimizing database performance requires...', 3, NOW() - INTERVAL '1 day', TRUE, 156),
('Working with Relationships', 'Foreign keys and relationships are...', 1, NULL, FALSE, 0);

INSERT INTO blog.comment (content, author_id, post_id, is_approved) VALUES
('Great introduction! This really helped me understand.', 2, 1, TRUE),
('Thanks for the clear explanations.', 3, 1, TRUE),
('Could you cover transactions in a future post?', 1, 2, TRUE),
('Excellent deep dive into PostgreSQL features.', 3, 2, TRUE);

-- Create a simple view for statistics
CREATE VIEW blog.author_stats AS
SELECT 
    a.id,
    a.first_name || ' ' || a.last_name AS full_name,
    a.email,
    COUNT(p.id) AS post_count,
    COUNT(CASE WHEN p.is_published THEN 1 END) AS published_count
FROM blog.author a
LEFT JOIN blog.post p ON a.id = p.author_id
GROUP BY a.id, a.first_name, a.last_name, a.email;
```

Create the database:

```sh
psql blog_tutorial -U tutorial_user -W -f tutorial_setup.sql
# Verify the setup
psql blog_tutorial -U tutorial_user -W -c "\dt blog.*"
```

### Step 2: Configure halfORM Connection

```bash
# Create config file
mkdir -p ~/.half_orm
cat > ~/.half_orm/blog_tutorial << EOF
[database]
name = blog_tutorial
user = tutorial_user
password = tutorial_pass
port = 5432
EOF
```

## Exploring the Database

### Step 3: Explore with CLI

Use the new CLI to explore your database:

```bash
# Inspect database structure
half_orm inspect blog_tutorial
```

Expected output:
```
📂 Schema: blog
  📋 author
  👁️ author_stats
  📋 comment
  📋 post

Total: 4 relations
   📋: 3 tables
   👁️: 1 view
```

### Step 4: Detailed Table Inspection

```bash
# Inspect specific table
half_orm inspect blog_tutorial blog.author
```

This shows complete table structure with columns, types, constraints, and foreign keys.

## Connecting to Your Database

### Step 5: First Connection

```python
from half_orm.model import Model

# Connect to the tutorial database
blog = Model('blog_tutorial')

print("🎉 Connected to blog_tutorial database!")
print(blog)
```

Expected output:
```
📋 Available relations for blog_tutorial:
r "blog"."author"
r "blog"."comment"
r "blog"."post"
v "blog"."author_stats"
```

## Creating Your First Relation Classes

### Step 6: Basic Relation Classes

```python
from half_orm.model import Model

blog = Model('blog_tutorial')

# Create relation classes
Author = blog.get_relation_class('blog.author')
Post = blog.get_relation_class('blog.post')
Comment = blog.get_relation_class('blog.comment')
AuthorStats = blog.get_relation_class('blog.author_stats')

# Explore table structure
print("📋 Author table structure:")
print(Author())
```

This displays detailed information about columns, constraints, and foreign keys.

## Your First CRUD Operations

### Important: NULL vs None

```python
from half_orm.null import NULL

# ❌ COMMON TRAP
Author(bio=None)   # Ignores bio field entirely
Author(bio=NULL)   # ✅ Filters WHERE bio IS NULL
```

### Step 7: Reading Data

```python
# Read all authors
print("👥 All authors:")
for author in Author().ho_select('first_name', 'last_name', 'email'):
    print(f"  📝 {author['first_name']} {author['last_name']} - {author['email']}")

# Count records
author_count = Author().ho_count()
print(f"\n🔢 Total authors: {author_count}")

# Get specific author
alice = Author(email='alice@example.com').ho_get()
print(f"\n🎯 Found: {alice.first_name} {alice.last_name}")

# Work with the view
print("\n📊 Author statistics:")
for stats in AuthorStats().ho_select('full_name', 'post_count', 'published_count'):
    print(f"  📈 {stats['full_name']}: {stats['post_count']} posts ({stats['published_count']} published)")
```

### Step 8: Creating Data

```python
# Create new author
new_author = Author(
    first_name='Emma',
    last_name='Wilson',
    email='emma@example.com',
    bio='Frontend developer passionate about user experience.',
    birth_date='1991-05-12'
)

# Check if author exists
if new_author.ho_is_empty():
    result = new_author.ho_insert()
    print(f"✅ Created: {result}")
else:
    print("ℹ️  Author already exists")
```

### Step 9: Updating Data

```python
# Update author bio
emma = Author(email='emma@example.com')
if not emma.ho_is_empty():
    emma.ho_update(bio='Frontend developer and UX designer.')
    print("✅ Updated Emma's bio")
```

### Step 10: Deleting Data

```python
# Delete author
Author(email='emma@example.com').ho_delete()
print("✅ Deleted Emma")
```

## Basic Filtering and Querying

### Step 11: Filtering Patterns

```python
# Exact match
alice = Author(email='alice@example.com').ho_get()

# Pattern matching
tech_authors = Author(bio=('ilike', '%tech%'))

# Date comparison
recent_posts = Post(published_at=('>', '2024-01-01'))

# Boolean filter
published_posts = Post(is_published=True)

# Ordering and limiting
popular_posts = (Post(is_published=True)
                .ho_order_by('view_count DESC')
                .ho_limit(3))

for post in popular_posts.ho_select('title', 'view_count'):
    print(f"🌟 {post['title']} - {post['view_count']} views")
```

### Step 12: Working with Relationships

```python
from half_orm.model import register

# Define custom classes with foreign key aliases
@register
class Author(blog.get_relation_class('blog.author')):
    Fkeys = {
        'posts': '_reverse_fkey_blog_tutorial_blog_post_author_id',
        'comments': '_reverse_fkey_blog_tutorial_blog_comment_author_id'
    }

@register
class Post(blog.get_relation_class('blog.post')):
    Fkeys = {
        'author': 'post_author_id_fkey',
        'comments': '_reverse_fkey_blog_tutorial_blog_comment_post_id'
    }

# Navigate relationships
alice = Author(email='alice@example.com').ho_get()
alice_posts = alice.posts()
print(f"📚 Alice has {alice_posts.ho_count()} posts")

# Get author from post
post = Post(id=1)
for author in post.author():
    print(f"✍️ Post author: {author['first_name']} {author['last_name']}")
```

## Understanding halfORM's Core Concepts

### Builder vs Executor Pattern

```python
# ✅ Build query first (no SQL executed)
query = (Post(is_published=True)
         .ho_order_by('published_at DESC')
         .ho_limit(5))

# ✅ Then execute (SQL runs now)
for post in query.ho_select('title', 'published_at'):
    print(f"📄 {post['title']}")

# ❌ Cannot chain after execution
# results = Post().ho_select('title')  # Returns generator
# results.ho_order_by('title')  # ERROR!
```

### SQL Transparency

```python
# See the generated SQL
query = Author(is_active=True).ho_order_by('last_name')
query.ho_mogrify()  # Shows SQL in console

# Then execute
for author in query.ho_select('first_name', 'last_name'):
    print(f"👤 {author['first_name']} {author['last_name']}")
```

## What's Next?

Congratulations! You've successfully:

- ✅ Set up a complete tutorial database with sample data
- ✅ Connected to PostgreSQL using halfORM
- ✅ Explored database structure with the new CLI
- ✅ Created relation classes for tables and views
- ✅ Performed all basic CRUD operations
- ✅ Used filtering and querying features
- ✅ Navigated relationships with custom classes
- ✅ Understood key halfORM concepts

In the next chapter, [Models & Relations](models-relations.md), you'll learn:

- How to create sophisticated custom relation classes
- Using the `@register` decorator for enhanced functionality
- Adding business logic to your data classes
- Best practices for organizing your halfORM code

---

**Ready to go deeper?** Continue to [Chapter 3: Models & Relations](models-relations.md)!

!!! tip "Practice Makes Perfect"
    Try modifying the examples above:
    
    - Create new authors and posts
    - Experiment with different filters
    - Try combining multiple conditions
    - Explore the comment table
    
    The best way to learn halfORM is by experimenting with real data!