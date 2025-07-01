# halfORM Fundamentals

This page covers the core concepts that underpin halfORM's design and behavior. Understanding these fundamentals is essential for working effectively with halfORM across all use cases.

!!! tip "When to Read This"
    - Before diving into complex queries or relationships
    - When you need to understand halfORM's philosophy
    - As a reference for core concepts mentioned throughout the documentation
    - **Required reading** before [Queries](./tutorial/queries.md) and [Foreign Keys](./tutorial/foreign-keys.md)

## Core Philosophy

### Database-First Approach

halfORM takes a **database-first** approach where your PostgreSQL schema is the source of truth:

```python
# ✅ halfORM approach: Schema exists, code adapts
# 1. Design schema in SQL
CREATE TABLE blog.author (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL
);

# 2. Connect and use immediately
from half_orm.model import Model
blog = Model('blog_tutorial')
Author = blog.get_relation_class('blog.author')  # Adapts to your schema
```

**Benefits:**
- No schema migrations to manage
- Leverage full PostgreSQL feature set
- Easy integration with existing databases
- Database evolution independent of code

### SQL Transparency

halfORM generates SQL that you can inspect and understand:

```python
query = Author(is_active=True).ho_order_by('name')

# See exactly what SQL will be executed
query.ho_mogrify()  # Sets the object to print the SQL when executed (debugging purpose)

# Execute when ready
results = list(query)
# Output: SELECT * FROM "blog"."author" WHERE "is_active" = TRUE ORDER BY "name"
```

**Benefits:**
- No hidden query magic
- Learning opportunity

## Query Execution Model

### Declarative Programming

halfORM follows a **declarative programming model** where you build query intentions first, then execute them when needed:

```python
from half_orm.model import Model

blog = Model('blog_tutorial')
Author = blog.get_relation_class('blog.author')

# 🎯 Declaration phase - no SQL executed yet
authors = Author(is_active=True)
gmail_authors = Author(email=('ilike', '%@gmail.com'))
ordered_authors = authors.ho_order_by('last_name')

# ⚡ Execution phase - SQL runs now
for author in ordered_authors:  # Query executes here
    print(author['first_name'])

# Alternative execution methods
author_list = list(ordered_authors)  # Executes here
author_count = ordered_authors.ho_count()  # Executes here
```

### Lazy Evaluation

Queries are **lazy** - they only execute when you actually need the data:

```python
# These build intentions (no SQL executed)
authors = Author(is_active=True)
posts = Post(is_published=True).ho_order_by('published_at DESC')
comments = Comment(is_approved=True)

# These execute SQL
list(authors)           # SELECT executed
for post in posts:      # SELECT executed
    pass
posts.ho_count()        # COUNT executed
posts.ho_is_empty()     # EXISTS executed
next(posts.ho_limit(1)) # SELECT LIMIT 1 executed
```

### The ho_get() Anti-Pattern

A common halfORM anti-pattern is calling `ho_get()` too early:

```python
# ❌ Anti-pattern - breaks the declarative flow
alice = Author(email='alice@example.com').ho_get()  # Forces execution
alice_posts = alice.posts_rfk()  # Now we're working with a singleton

# ✅ Better - keep building intentions
alice = Author(email='alice@example.com')  # Just an intention
alice_posts = alice.posts_rfk(is_published=True)  # Still building
popular_posts = alice_posts.ho_order_by('view_count DESC')  # Still building

# Execute when ready
for post in popular_posts:  # Query executes here
    print(post['title'])
```

## Object-as-Filter Pattern

### The Core Concept

In halfORM, **the object IS the filter**. When you create a relation instance with parameters, you're defining a subset of rows:

```python
# These are all "filters" - they represent subsets of data
all_authors = Author()                           # All authors
active_authors = Author(is_active=True)          # Only active authors
gmail_authors = Author(email=('ilike', '%@gmail.com'))  # Only Gmail users
young_authors = Author(birth_date=('>', '1990-01-01'))  # Born after 1990
```

### Constraint Syntax

halfORM supports two forms of constraints:

#### 1. Single Value (Exact Match)
```python
# These create equality constraints
Author(name='John')           # WHERE name = 'John'
Author(is_active=True)        # WHERE is_active = TRUE
Author(age=25)                # WHERE age = 25
```

#### 2. Tuple (Operator, Value)
```python
# These create custom comparison constraints
Author(age=('>', 18))         # WHERE age > 18
Author(name=('ilike', 'j%'))  # WHERE name ILIKE 'j%'
Author(birth_date=('between', ('1980-01-01', '1990-01-01')))  # WHERE birth_date BETWEEN ...
```

### Common Operators

| Operator | SQL Equivalent | Example | Description |
|----------|----------------|---------|-------------|
| `=` (default) | `=` | `Author(name='John')` | Exact equality |
| `('>', value)` | `>` | `Author(age=('>', 18))` | Greater than |
| `('<', value)` | `<` | `Author(age=('<', 65))` | Less than |
| `('>=', value)` | `>=` | `Author(age=('>=', 21))` | Greater than or equal |
| `('<=', value)` | `<=` | `Author(age=('<=', 65))` | Less than or equal |
| `('!=', value)` | `!=` | `Author(status=('!=', 'inactive'))` | Not equal |
| `('like', pattern)` | `LIKE` | `Author(name=('like', 'John%'))` | Case-sensitive pattern |
| `('ilike', pattern)` | `ILIKE` | `Author(email=('ilike', '%@gmail.com'))` | Case-insensitive pattern |
| `('in', list)` | `IN` | `Author(id=('in', [1, 2, 3]))` | Value in list |
| `('between', (a, b))` | `BETWEEN` | `Author(age=('between', (18, 65)))` | Value between range |

## Relations as Python Sets

### Set Theory in halfORM

halfORM Relations behave like mathematical sets, supporting all standard set operations:

```python
Author = blog.get_relation_class('blog.author')

# Define some author sets
all_authors = Author()
active_authors = Author(is_active=True)
gmail_authors = Author(email=('ilike', '%@gmail.com'))
old_authors = Author(birth_date=('<', '1980-01-01'))
```

### Set Operations

```python
# Union (OR) - authors that are active OR use gmail
active_or_gmail = active_authors | gmail_authors

# Intersection (AND) - authors that are active AND use gmail  
active_gmail = active_authors & gmail_authors

# Difference - active authors who don't use gmail
active_not_gmail = active_authors - gmail_authors

# Complement - non-active authors
inactive_authors = -active_authors

# Symmetric difference - authors that are either active OR use gmail, but not both
either_but_not_both = active_authors ^ gmail_authors
```

### Set Membership and Equality

```python
# Membership testing
young_authors = Author(birth_date=('>', '1990-01-01'))
alice = Author(email='alice@example.com').ho_get()
if alice in young_authors:
    print("Alice is young")

# Set equality and comparison  
tech_authors = Author(bio=('ilike', '%tech%'))
if active_authors == tech_authors:
    print("All active authors are tech-focused")

# Subset testing
if young_authors <= all_authors:  # young_authors ⊆ all_authors
    print("Young authors are a subset of all authors")
```

## Schema Requirements

### Explicit Schema Names

halfORM always requires the full `schema.table` format, even for tables in PostgreSQL's default `public` schema:

```python
# ✅ Correct - always include schema name
Author = blog.get_relation_class('blog.author')
Product = blog.get_relation_class('inventory.products')
User = blog.get_relation_class('public.users')  # Even for public schema

# ❌ Wrong - will raise MissingSchemaInName error
Author = blog.get_relation_class('author')
User = blog.get_relation_class('users')
```

**Why explicit schemas?**
- Prevents ambiguity when tables exist in multiple schemas
- Makes code more maintainable and clear
- Enforces best practices for database organization

### PostgreSQL Metadata Integration

halfORM leverages PostgreSQL's rich metadata system:

```python
# Comments become part of the relation documentation
Author = blog.get_relation_class('blog.author')
print(Author())  # Shows table and column comments

# Constraints are automatically detected
print(Author()._ho_pkey)  # Primary key columns
print(Author()._ho_ukeys)  # Unique constraints
print(Author()._ho_fkeys)  # Foreign key relationships
```

## Method Naming Convention

### The ho_ Prefix

All halfORM-Relation specific methods use the `ho_` prefix to avoid conflicts with business methods:

```python
# halfORM methods (always prefixed)
author.ho_get()         # Get single record
author.ho_insert()      # Insert record
author.ho_update()      # Update record
author.ho_delete()      # Delete record
author.ho_count()       # Count records
author.ho_select()      # Select with column specification
author.ho_order_by()    # Add ordering
author.ho_limit()       # Add limit
author.ho_offset()      # Add offset
author.ho_is_empty()    # Check if result set is empty

class Author(blog.get_relation_class('blog.author')):
    def count(self):
        # ...
    def select(self):
        # ...
```

**Benefits:**
- No conflicts with method names
- Clear distinction between halfORM operations and business logic
- Consistent API across all relation classes

## Database-First Strategy

### When to Use SQL Views

When halfORM queries become too complex, consider creating database views:

```sql
-- Instead of complex halfORM queries, create a view
CREATE VIEW blog.author_stats AS
SELECT 
    a.*,
    COUNT(p.id) as post_count,
    COUNT(c.id) as comment_count,
    AVG(p.view_count) as avg_post_views
FROM blog.author a
LEFT JOIN blog.post p ON a.id = p.author_id  
LEFT JOIN blog.comment c ON a.id = c.author_id
GROUP BY a.id;
```

```python
# Then use the view in halfORM
AuthorStats = blog.get_relation_class('blog.author_stats')

# Simple and efficient
top_authors = (AuthorStats(post_count=('>', 5))
               .ho_order_by('avg_post_views DESC')
               .ho_limit(10))
```

### When to Use SQL Functions

For complex calculations, use PostgreSQL functions:

```sql
-- Create a function for complex business logic
CREATE OR REPLACE FUNCTION blog.get_trending_posts(days_back INTEGER)
RETURNS TABLE(post_id INTEGER, score NUMERIC) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        (p.view_count::NUMERIC / EXTRACT(days FROM NOW() - p.published_at)) as score
    FROM blog.post p
    WHERE p.published_at > NOW() - INTERVAL '%s days', days_back
    AND p.is_published = TRUE
    ORDER BY score DESC;
END;
$$ LANGUAGE plpgsql;
```

```python
# Use the function from halfORM
trending = blog.execute_function('blog.get_trending_posts', 30)
for post_data in trending:
    print(f"Post {post_data['post_id']}: score {post_data['score']}")
```

## Performance Principles

### Lazy Loading by Default

halfORM doesn't automatically load related data, giving you control over performance:

```python
# This doesn't load posts
author = Author(email='alice@example.com')

# This creates a new query for posts
posts = author.posts_rfk()

# This executes the posts query
post_count = posts.ho_count()
```

### Efficient Field Selection

Only select the fields you need:

```python
# ❌ Loads all columns (can be wasteful for large tables)
for author in Author():
    print(author['name'])

# ✅ Loads only needed columns
for author in Author().ho_select('first_name', 'last_name'):
    print(f"{author['first_name']} {author['last_name']}")
```

### Count vs Loading

Use count operations instead of loading data when you just need numbers:

```python
# ✅ Efficient - just counts
if Post(is_published=False).ho_count() > 0:
    print("Drafts exist")

# ❌ Inefficient - loads all draft posts
if len(list(Post(is_published=False))) > 0:
    print("Drafts exist")
```

!!! tip "Count for large tables"
    Counts can be slow in PostgreSQL with large tables

## Summary

These fundamentals form the foundation of all halfORM operations:

1. **Database-First**: Schema in SQL, code adapts
2. **SQL Transparency**: See and understand generated queries
3. **Declarative Queries**: Build intentions, execute when needed
4. **Object-as-Filter**: Instances represent data subsets
5. **Set Operations**: Relations behave like mathematical sets
6. **Explicit Schemas**: Always use `schema.table` format
7. **ho_ Prefix**: Clear method naming convention
8. **Lazy Evaluation**: Queries execute only when needed

Understanding these concepts will make all other halfORM features more intuitive and help you write more efficient, maintainable code.

!!! tip "Next Steps"
    Now that you understand the fundamentals, explore:
    
    - **[Queries](queries.md)** - Advanced filtering and query patterns
    - **[Foreign Keys](foreign-keys.md)** - Relationship navigation
    - **[Models & Relations](models-relations.md)** - Custom classes and business logic