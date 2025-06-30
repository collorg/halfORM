# Chapter 3: Models & Relations

In the previous chapter, you learned how to connect to databases and perform basic CRUD operations. Now we'll dive deeper into halfORM's core concepts: Models and custom Relation classes. You'll learn how to add business logic to your data classes and create a more maintainable codebase.

## Chapter Objectives

By the end of this chapter, you'll understand:

- **Model architecture** - How halfORM organizes database connections and relation classes
- **Custom relation classes** - Creating classes with business logic and clean interfaces
- **The `@register` decorator** - Overriding auto-generated classes with your custom implementations
- **Class organization** - Best practices for structuring your halfORM code
- **Inheritance patterns** - Working with PostgreSQL table inheritance

## Understanding the Model Class

The `Model` class is halfORM's central component. It represents a connection to a specific PostgreSQL database and serves as a factory for relation classes.

!!! info "API Reference"
    For complete documentation of all Model methods and properties, see the [Model API Reference](../api/model.md).

### Model Responsibilities

```python
from half_orm.model import Model

# Connect to database
blog = Model('blog_tutorial')

# The model handles:
# 1. Database connection management
# 2. Metadata loading and caching
# 3. Relation class generation and caching
# 4. Transaction coordination
```

### Model as a Relation Factory

When you call `get_relation_class()`, the model returns the generated class that inherits from `Relation`. Classes are created once and cached:

```python
# Each call returns the same cached class
Author1 = blog.get_relation_class('blog.author')
Author2 = blog.get_relation_class('blog.author')
print(Author1 is Author2)  # → True (same class object)

print(Author1.__name__)  # → 'Table_BlogTutorialBlogAuthor'
print(Author1.__bases__)  # → (<class 'half_orm.relation.Relation'>,)

# You can inspect the generated class
print(Author1())  # Shows complete table structure
```

!!! important "Schema Names Required"
    halfORM always requires the full `schema.table` format, even for tables in PostgreSQL's default `public` schema:
    
    ```python
    # ✅ Correct - explicit schema name
    User = blog.get_relation_class('public.users')
    Product = blog.get_relation_class('inventory.products')
    
    # ❌ Wrong - will raise MissingSchemaInName error
    User = blog.get_relation_class('users')
    ```
    
    This explicit naming prevents ambiguity when you have tables with the same name in different schemas.

### Model Metadata

Models automatically discover and cache database structure:

```python
# Explore what's in your database
print(blog)  # Shows all relations

# Check if a relation exists
if blog.has_relation('blog.author'):
    Author = blog.get_relation_class('blog.author')

# Get detailed metadata
relations = blog.desc()  # List of all relations with inheritance info
```

## Auto-Generated Relation Classes

When you call `get_relation_class()`, halfORM generates a class with all the necessary attributes and methods based on your database schema.

!!! info "API Reference"
    For complete documentation of all Relation methods and properties, see the [Relation API Reference](../api/relation.md).

### What Gets Generated Automatically

```python
Author = blog.get_relation_class('blog.author')

# Fields become attributes
author = Author()
print(author.first_name)  # → Field object
print(author.email)       # → Field object

# Foreign keys are available
print(author._ho_fkeys.keys())  # → All available foreign keys

# Metadata is attached
print(author._ho_metadata['description'])  # → Table comment
print(author._ho_pkey)  # → Primary key fields
```

### Working with Auto-Generated Classes

```python
# You can use auto-generated classes directly
Author = blog.get_relation_class('blog.author')
Post = blog.get_relation_class('blog.post')

# For tables in the public schema, include 'public.'
User = blog.get_relation_class('public.users')

# Create and manipulate data
alice = Author(
    first_name='Alice', 
    last_name='Johnson', 
    email='alice@example.com'
).ho_insert()

# Navigate relationships using the full foreign key names
alice_posts = alice._ho_fkeys['_reverse_fkey_blog_tutorial_blog_post_author_id']()
print(f"Alice has {alice_posts.ho_count()} posts")
```

**The Problem**: Foreign key names are long and hard to remember. Business logic gets scattered across your application.

## Creating Custom Relation Classes

Custom relation classes let you add business logic, create readable foreign key aliases, and encapsulate domain-specific operations.

### Basic Custom Class Structure

```python
from half_orm.model import Model

blog = Model('blog_tutorial')

class Author(blog.get_relation_class('blog.author')):
    """Custom Author class with business methods"""
    
    # Clean foreign key aliases
    Fkeys = {
        'posts_rfk': '_reverse_fkey_blog_tutorial_blog_post_author_id',
        'comments_rfk': '_reverse_fkey_blog_tutorial_blog_comment_author_id'
    }
    
    def get_full_name(self):
        """Return author's full name"""
        return f"{self.first_name.value} {self.last_name.value}"
    
    def get_post_count(self):
        """Get total number of posts by this author"""
        return self.posts_rfk().ho_count()
    
    def create_post(self, title, content):
        """Create a new post for this author"""
        return self.posts_rfk(
            title=title,
            content=content
        ).ho_insert()

# Usage
alice = Author(email='alice@example.com').ho_get()
print(alice.get_full_name())  # → "Alice Johnson"
print(f"Posts: {alice.get_post_count()}")  # → "Posts: 3"

# Clean foreign key access
for post in alice.posts_rfk():
    print(post['title'])
```

### The Fkeys Dictionary

The `Fkeys` dictionary maps friendly names to actual foreign key constraint names:

```python
class Author(blog.get_relation_class('blog.author')):
    Fkeys = {
        # Alias: Actual constraint name
        'posts_rfk': '_reverse_fkey_blog_tutorial_blog_post_author_id',
        'comments_rfk': '_reverse_fkey_blog_tutorial_blog_comment_author_id'
    }

# Now you can use clean names
author = Author().ho_get()
author.posts_rfk()     # Instead of author._ho_fkeys['_reverse_fkey_...']()
author.comments_rfk()  # Much more readable!
```

**Pro Tip**: When you print a relation class (`print(Author())`), halfORM shows you the exact foreign key names to copy into your `Fkeys` dictionary.

### Adding Business Logic

Custom classes are perfect for encapsulating domain logic:

```python
from datetime import datetime, timedelta

class Author(blog.get_relation_class('blog.author')):
    Fkeys = {
        'posts_rfk': '_reverse_fkey_blog_tutorial_blog_post_author_id',
        'comments_rfk': '_reverse_fkey_blog_tutorial_blog_comment_author_id'
    }
    
    def is_active_writer(self, days=30):
        """Check if author has posted recently"""
        cutoff = datetime.now() - timedelta(days=days)
        recent_posts = self.posts_rfk(created_at=('>', cutoff))
        return recent_posts.ho_count() > 0
    
    def get_statistics(self):
        """Get comprehensive author statistics"""
        all_posts = self.posts_rfk()
        published_posts = all_posts(is_published=True)
        
        return {
            'total_posts': all_posts.ho_count(),
            'published_posts': published_posts.ho_count(),
            'draft_posts': all_posts(is_published=False).ho_count(),
            'total_comments': self.comments_rfk().ho_count()
        }
    
    def publish_all_drafts(self):
        """Publish all draft posts for this author"""
        drafts = self.posts_rfk(is_published=False)
        return drafts.ho_update(
            is_published=True,
            published_at=datetime.now()
        )

# Usage
alice = Author(email='alice@example.com').ho_get()

if alice.is_active_writer():
    stats = alice.get_statistics()
    print(f"Alice has {stats['published_posts']} published posts")
    
    # Publish remaining drafts
    if stats['draft_posts'] > 0:
        alice.publish_all_drafts()
        print(f"Published {stats['draft_posts']} draft posts")
```

## The @register Decorator

The `@register` decorator is halfORM's powerful feature that replaces the auto-generated base class with your custom class in the model's class cache. This makes your custom classes the default whenever that relation is accessed, including through foreign key navigation.

### Without @register

```python
# Regular custom class
class Author(blog.get_relation_class('blog.author')):
    def get_full_name(self):
        return f"{self.first_name.value} {self.last_name.value}"

class Post(blog.get_relation_class('blog.post')):
    Fkeys = {'author_fk': 'post_author_id_fkey'}

# Problem: Foreign keys return generic classes
post = Post(title='My Post').ho_get()
author = post.author_fk().ho_get()  # Returns generic Author class
# author.get_full_name()  # ❌ Method doesn't exist!
```

### With @register

```python
from half_orm.model import register

@register
class Author(blog.get_relation_class('blog.author')):
    Fkeys = {
        'posts_rfk': '_reverse_fkey_blog_tutorial_blog_post_author_id',
        'comments_rfk': '_reverse_fkey_blog_tutorial_blog_comment_author_id'
    }
    
    def get_full_name(self):
        return f"{self.first_name.value} {self.last_name.value}"
    
    def create_post(self, title, content):
        return self.posts_rfk(title=title, content=content).ho_insert()

@register  
class Post(blog.get_relation_class('blog.post')):
    Fkeys = {'author_fk': 'post_author_id_fkey'}
    
    def get_author_name(self):
        return self.author_fk().ho_get().get_full_name()

# Magic: Foreign keys now return YOUR custom classes!
post = Post(title='My Post').ho_get()
author = post.author_fk().ho_get()  # Returns YOUR Author class!
print(author.get_full_name())       # ✅ Method available!

# Works in both directions
alice = Author(email='alice@example.com').ho_get()
for post in alice.posts_rfk():  # Each post is YOUR Post class
    post_obj = Post(**post)
    print(post_obj.get_author_name())  # Your custom methods work!
```

### How @register Works

When you use `@register`, halfORM:

1. **Replaces the auto-generated class** in the model's class cache with your custom class
2. **Returns your class** whenever that relation is requested via `get_relation_class()`
3. **Uses your class** in foreign key navigation automatically
4. **Preserves your methods** and custom `Fkeys` across all relation access

```python
# Before registration
Author1 = blog.get_relation_class('blog.author')  # Auto-generated class
print(Author1.__name__)  # → 'Table_BlogTutorialBlogAuthor'

# Registration happens at import time
@register
class Author(blog.get_relation_class('blog.author')):
    def get_full_name(self):
        return f"{self.first_name.value} {self.last_name.value}"

# After registration - same call now returns YOUR class
Author2 = blog.get_relation_class('blog.author')  # Returns your Author class
print(Author2 is Author)  # → True (same class object)
```

## Putting It All Together

Here are focused examples showing the key concepts:

### Simple Custom Class with Business Logic

```python
from half_orm.model import Model

blog = Model('blog_tutorial')

class Author(blog.get_relation_class('blog.author')):
    Fkeys = {'posts_rfk': '_reverse_fkey_blog_tutorial_blog_post_author_id'}
    
    def get_full_name(self):
        return f"{self.first_name.value} {self.last_name.value}"
    
    def create_post(self, title, content):
        return self.posts_rfk(title=title, content=content).ho_insert()

# Usage
alice = Author(email='alice@example.com').ho_get()
print(alice.get_full_name())  # "Alice Johnson"
alice.create_post("My First Post", "Hello World!")
```

### Using @register for Automatic Resolution

```python
from half_orm.model import register

@register  # This makes your class the default
class Author(blog.get_relation_class('blog.author')):
    Fkeys = {'posts_rfk': '_reverse_fkey_blog_tutorial_blog_post_author_id'}
    
    def get_post_count(self):
        return self.posts_rfk().ho_count()

@register
class Post(blog.get_relation_class('blog.post')):
    Fkeys = {'author_fk': 'post_author_id_fkey'}

# Magic: Foreign keys return YOUR classes with YOUR methods
post = Post(title='Welcome').ho_get()
author = post.author_fk().ho_get()  # Returns YOUR Author class!
print(f"Posts by this author: {author.get_post_count()}")  # Custom method works!
```

### Working with PostgreSQL Inheritance

halfORM handles PostgreSQL table inheritance naturally:

```python
# PostgreSQL: CREATE TABLE blog.event (...) INHERITS (blog.post);

@register
class Post(blog.get_relation_class('blog.post')):
    Fkeys = {'author_fk': 'post_author_id_fkey'}

@register  
class Event(blog.get_relation_class('blog.event')):
    # Inherits all Post functionality + event-specific fields
    Fkeys = {'author_fk': 'event_author_id_fkey'}
    
    def is_upcoming(self):
        from datetime import datetime
        return self.begin.value > datetime.now()

# Events are also Posts
event = Event(title='Conference').ho_get()
print(event.title.value)  # Inherited from Post
print(event.is_upcoming())  # Event-specific method
```

## Best Practices

### 1. Use @register for Production Code

```python
# ❌ Don't: Manual class usage
Author = blog.get_relation_class('blog.author')
author = Author().ho_get()

# ✅ Do: Register your classes
@register
class Author(blog.get_relation_class('blog.author')):
    pass

# Now all foreign key navigation uses your class automatically
```

### 2. Keep Business Logic in Relation Classes

```python
@register
class Order(blog.get_relation_class('shop.order')):
    Fkeys = {'items_rfk': '_reverse_fkey_shop_order_item_order_id'}
    
    def calculate_total(self):
        """Business logic belongs in the relation class"""
        total = 0
        for item in self.items_rfk():
            total += item['price'] * item['quantity']
        return total
    
    def can_be_cancelled(self):
        """Domain rules encapsulated in the class"""
        return self.status.value in ['pending', 'confirmed']
```

### 3. Use Descriptive Fkey Aliases

```python
class Author(blog.get_relation_class('blog.author')):
    Fkeys = {
        # ✅ Clear and descriptive
        'posts': '_reverse_fkey_blog_tutorial_blog_post_author_id',
        'comments': '_reverse_fkey_blog_tutorial_blog_comment_author_id',
        
        # ❌ Avoid unclear names  
        # 'rfk1': '_reverse_fkey_blog_tutorial_blog_post_author_id',
        # 'data': '_reverse_fkey_blog_tutorial_blog_comment_author_id'
    }
```

### 4. Organize Your Classes

```python
# blog_models.py
from half_orm.model import Model, register

blog = Model('blog_tutorial')

@register
class Author(blog.get_relation_class('blog.author')):
    """Authors who write posts and comments"""
    Fkeys = {'posts': '_reverse_fkey_blog_tutorial_blog_post_author_id'}
    
    def get_stats(self):
        return {'posts': self.posts().ho_count()}

@register  
class Post(blog.get_relation_class('blog.post')):
    """Blog posts with content"""
    Fkeys = {'author': 'post_author_id_fkey'}
    
    def publish(self):
        return self.ho_update(is_published=True)

# Usage in other modules
from blog_models import Author, Post

alice = Author(email='alice@example.com').ho_get()
stats = alice.get_stats()
```

## Chapter Summary

Congratulations! You've mastered the core concepts of halfORM's architecture. Let's recap what you've learned:

### ✅ Key Concepts Mastered

**Model Class Architecture**
- The Model manages database connections and class caching
- `get_relation_class()` returns cached classes, not new instances
- Models automatically discover and cache database metadata

**Auto-Generated Relation Classes**
- halfORM creates classes with all table fields as attributes
- Foreign keys are available via long constraint names
- Basic CRUD operations work immediately

**Custom Relation Classes**
- Add business logic methods to your data classes
- Use `Fkeys` dictionary for clean foreign key aliases
- Encapsulate domain-specific operations

**The @register Decorator**
- Replaces auto-generated classes with your custom classes
- Makes foreign key navigation return YOUR classes automatically
- Enables clean, maintainable code architecture

### 🎯 Skills You Can Now Apply

- Create custom relation classes with business methods
- Set up clean foreign key aliases using `Fkeys`
- Use `@register` to make your classes the default
- Organize your halfORM code effectively
- Work with PostgreSQL table inheritance

### 💡 Best Practices You've Learned

- Use `@register` for production code
- Keep business logic in relation classes
- Choose descriptive names for `Fkeys` aliases
- Organize classes in dedicated modules

## What's Next?

Now that you understand Models and Relations, you're ready to master relationship navigation. In the next chapter, [Foreign Keys](foreign-keys.md), you'll learn:

- **Advanced navigation patterns** - Chaining relationships efficiently
- **Complex relationship handling** - Many-to-many, self-references
- **Query optimization** - Reducing database calls across tables
- **Relationship constraints** - Using foreign keys for filtering

The foreign key system is where halfORM really shines, letting you navigate complex database relationships with intuitive Python syntax.

!!! tip "Additional Resources"
    - **[Model API Reference](../api/model.md)** - Complete Model class documentation
    - **[Relation API Reference](../api/relation.md)** - All Relation methods and properties  
    - **[Examples](../examples/index.md)** - Real-world usage patterns

---

**Ready to master relationships?** Continue to [Chapter 4: Foreign Keys](foreign-keys.md)!