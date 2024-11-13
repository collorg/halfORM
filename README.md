# `half_orm`: A simple PostgreSQL to Python mapper

[![PyPI version](https://img.shields.io/pypi/l/half_orm?color=green)](https://pypi.org/project/half-orm/)
[![PyPI version](https://img.shields.io/pypi/v/half_orm)](https://pypi.org/project/half-orm/)
[![Python versions](https://img.shields.io/badge/Python-%20&ge;%203.7-blue)](https://www.python.org)
[![PostgreSQL versions](https://img.shields.io/badge/PostgreSQL-%20&ge;%209.6-blue)](https://www.postgresql.org)
[![Test on different versions of Python](https://github.com/collorg/halfORM/actions/workflows/python-package.yml/badge.svg)](https://github.com/collorg/halfORM/actions/workflows/python-package.yml)
[![Test on different versions of PostgreSQL](https://github.com/collorg/halfORM/actions/workflows/postgresql-releases.yml/badge.svg)](https://github.com/collorg/halfORM/actions/workflows/postgresql-releases.yml)
[![Coverage Status](https://coveralls.io/repos/github/collorg/halfORM/badge.svg?branch=main)](https://coveralls.io/github/collorg/halfORM?branch=main)
[![Downloads](https://static.pepy.tech/badge/half_orm)](https://clickpy.clickhouse.com/dashboard/half-orm)
[![Contributors](https://img.shields.io/github/contributors/collorg/halform)](https://github.com/collorg/halfORM/graphs/contributors)

Nowadays, most applications require interacting with a relational database. While full-fledged ORMs like SQLAlchemy are very powerful, their complexity, steep learning curve, and some of their limitations can be a hindrance. This is the context in which half_orm was born, a minimalist ORM specifically designed for PostgreSQL. The main motivation is to allow modeling the database directly in SQL, taking full advantage of the capabilities offered by the PostgreSQL engine (triggers, views, functions, stored procedures, inheritance handling...), while avoiding the "impedance mismatch" issues, loss of control over generated SQL, and rigidity encountered with full-fledged ORMs that model the schema at the object level. Half_orm intentionally excludes the DDL aspects (schema creation) of the SQL language. The goal is to provide a lightweight abstraction layer over standard SQL queries while maintaining transparent access to the underlying database engine. With half_orm, writing INSERT, SELECT, UPDATE, and DELETE queries becomes as simple as with SQL, but in the comfort of Python. Its operation aims to be intuitive thanks to a lean API that emphasizes productivity and code readability.

Here is what coding with `half_orm` looks like :

```py
from half_orm.model import Model
from half_orm.relation import singleton

halftest = Model('halftest') # We connect to the PostgreSQL database
# print(halftest) to get the list of relations in the database

class Post(halftest.get_relation_class('blog.post')):
    """blog.post is a table of the halftest database (<schema>.<relation>)
    To get a full description of the relation, use print(Post())
    """
    #  The Fkeys template is provided by print(Post()). Just fill in the keys names.
    Fkeys = {
        'comments_rfk': '_reverse_fkey_halftest_blog_comment_post_id', # a post is referenced by comments
        'author_fk': 'author' # the post references a person
    }

class Person(halftest.get_relation_class('actor.person')):
    Fkeys = {
        'posts_rfk': '_reverse_fkey_halftest_blog_post_author_first_name_author_last_name_author_birth_date',
        'comments_rfk': '_reverse_fkey_halftest_blog_comment_author_id'
    }
    @singleton # This ensures that the author of the post is well defined.
    def add_post(self, title: str=None, content: str=None) -> dict:
        return self.posts_rfk(title=title, content=content).ho_insert()
    @singleton
    def add_comment(self, post: Post=None, content: str=None) -> dict:
        return self.comments_rfk(content=content, post_id=post.id.value).ho_insert()

def main():
    gaston = Person(last_name='Lagaffe', first_name='Gaston', birth_date='1957-02-28')
    gaston.ho_delete()
    if gaston.ho_is_empty(): # gaston defines a subset of the actor.person table.
        gaston.ho_insert()
    post = Post(**gaston.add_post(title='Easy', content='halfORM is fun!'))
    gaston.add_comment(content='This is a comment on the newly created post.', post=post)
    print(list(post.comments_rfk())) # The relational objects are iterators
    post.ho_update(title='Super easy')
    gaston.ho_delete()
```

If you want to build or patch a model, see the [`half_orm packager`](#next-hop-the-gitops-half_orm-packager-wipalpha).

# Tutorial: Learn `half_orm` in half an hour



## Install `half_orm`

run `pip install half_orm` in a virtual environment.

### Set your HALFORM_CONF_DIR

Create a directory to store your connection files and set the shell variable `HALFORM_CONF_DIR`
(by default, `half_orm` looks in the /etc/half_orm directory):

```sh
% mkdir ~/.half_orm
% export HALFORM_CONF_DIR=~/.half_orm
```

> Set your HALFORM_CONF_DIR for windows users:
> - select settings in the menu
> - search for "variable"
> - select "Edit environment variables for your account"

Create a connection file in the `$HALFORM_CONF_DIR` containing the following information (with your values):

```ini
[database]
name = db_name
user = username
password = password
host = localhost
port = 5432
```

You are ready to go!
## Connect to the database

```py
>>> from half_orm.model import Model
>>> my_db = Model('my_database')
```

The `my_database` is the name of the connexion file. It will be fetched in the directory referenced by
the environment variable `HALFORM_CONF_DIR` if defined, in `/etc/half_orm` otherwise.


## Get a rapid description of the database structure

Once you are connected, you can easily have an overview of the structure of the database:

```py
print(my_db)
```

It displays as many lines as there are relations, views or materialized views in your
database. Each row has the form:

```
<relation type> <"schema name"."relation name">
```

Where `relation type` is one of `r`, `p`, `v`, `m`, `f`:

* `r` for a relation,
* `p` for a partitioned table,
* `v` for a view,
* `m` for a materialized view,
* `f` for foreign data.

for instance (using the halftest database):

```
r "actor"."person"
r "blog"."comment"
r "blog"."event"
r "blog"."post"
v "blog.view"."post_comment"
```

**Note**: We only allow dots in schema names.

## Check if a relation exists in the database

```py
>>> my_db.has_relation('blog.view.post_comment')
True
```

## Get the class of a relation (the `Model.get_relation_class` method)

To work with a table of your database, you must instanciate the corresponding class:

```py
class Person(halftest.get_relation_class('actor.person')):
    pass
class PostComment(halftest.get_relation_class('blog.view.post_comment')):
    pass
```

The argument passed to `get_relation_class` is as string of the form:
`<schema_name>.<relation_name>`.

**Note**: Again, dots are only allowed in schema names.

To get a full description of the corresponding relation, print an instance of the class:

```py
>>> print(Person())
```
```
DATABASE: halftest
SCHEMA: actor
TABLE: person

DESCRIPTION:
The table actor.person contains the persons of the blogging system.
The id attribute is a serial. Just pass first_name, last_name and birth_date
to insert a new person.
FIELDS:
- id:         (int4) NOT NULL
- first_name: (text) NOT NULL
- last_name:  (text) NOT NULL
- birth_date: (date) NOT NULL

PRIMARY KEY (first_name, last_name, birth_date)
UNIQUE CONSTRAINT (id)
UNIQUE CONSTRAINT (first_name)
FOREIGN KEYS:
- _reverse_fkey_halftest_blog_comment_author_id: ("id")
 ↳ "halftest":"blog"."comment"(author_id)
- _reverse_fkey_halftest_blog_event_author_first_name_author_last_name_author_birth_date: ("first_name", "last_name", "birth_date")
 ↳ "halftest":"blog"."event"(author_first_name, author_last_name, author_birth_date)
- _reverse_fkey_halftest_blog_post_author_first_name_author_last_name_author_birth_date: ("first_name", "last_name", "birth_date")
 ↳ "halftest":"blog"."post"(author_first_name, author_last_name, author_birth_date)

To use the foreign keys as direct attributes of the class, copy/paste the Fkeys below into
your code as a class attribute and replace the empty string key(s) with the alias(es) you
want to use. The aliases must be unique and different from any of the column names. Empty
string keys are ignored.

Fkeys = {
    '': '_reverse_fkey_halftest_blog_comment_author_id',
    '': '_reverse_fkey_halftest_blog_event_author_first_name_author_last_name_author_birth_date',
    '': '_reverse_fkey_halftest_blog_post_author_first_name_author_last_name_author_birth_date',
}
```

It provides you with information extracted from the database metadata:

* description: the comment on the relationship if there is one,
* fields: the list of columns, their types and contraints
* foreign keys: the list of FKs if any. A `_reverse_*` FK is a FK made on the current relation.


## Constraining a relation

When you instantiate an object with no arguments, its intent corresponds to all the data present in the corresponding relation.
`Person()` represents the set of persons contained in the `actor.person` table (i.e., there is no constraint on the set).

To define a subset, you need to specify constraints on the values of the fields/columns:
* with a single value for an exact match,
* with a tuple of the form `(comp, value)` otherwise.
The `comp` value is either a SQL
[comparison operator](https://www.postgresql.org/docs/current/static/functions-comparison.html) or a [pattern matching operator (like or POSIX regular expression)](https://www.postgresql.org/docs/current/static/functions-matching.html).

You can constrain a relation object at instanciation:

```py
Person(last_name='Lagaffe', first_name='Gaston', birth_date='1957-02-28')
Person(last_name=('ilike', '_a%'))
Person(birth_date='1957-02-28')
```

You can also constrain an instanciated object using the `Field.set` method:

```py
gaston = Person()
gaston.last_name.set(('ilike', 'l%'))
gaston.first_name.set('Gaston')
```

`half_orm` prevents you from making typos:

```py
gaston(lost_name='Lagaffe')
# raises a half_orm.relation_errors.IsFrozenError Exception
```

# DML. The `ho_insert`, `ho_update`, `ho_delete`, `ho_select` methods.

These methods trigger their corresponding SQL querie on the database.
For debugging purposes, you can print the SQL query built
by half_orm when the DML method is invoked using the ho_mogrify() method.

```py
people.ho_mogrify()
people.ho_select()
```

## ho_insert
To insert a tuple in the relation, use the `ho_insert` method as shown below:
```py
Person(last_name='Lagaffe', first_name='Gaston', birth_date='1957-02-28').ho_insert()
```

By default, `ho_insert` returns the inserted row as a dict:

```py
lagaffe = Person(last_name='Lagaffe', first_name='Gaston', birth_date='1957-02-28')
lagaffe_id = lagaffe.ho_insert()['id']
```

As of version 0.13, the `Relation.ho_transaction` decorator is replaced by the `transaction`
decorator. It uses the new `Transaction(<model>)` context manager:

```py
from half_orm.relation import transaction
# [...]

class Person(halftest.get_relation_class('actor.person')):
    # [...]

    @transaction
    def insert_many(self, *data):
        """Insert serveral people in a single transaction."""
        for d_pers in data:
            self(**d_pers).ho_insert()

```

```py
people = Person()
people.insert_many(*[
    {'last_name':'Lagaffe', 'first_name':'Gaston', 'birth_date':'1957-02-28'},
    {'last_name':'Fricotin', 'first_name':'Bibi', 'birth_date':'1924-10-05'},
    {'last_name':'Maltese', 'first_name':'Corto', 'birth_date':'1975-01-07'},
    {'last_name':'Talon', 'first_name':'Achile', 'birth_date':'1963-11-07'},
    {'last_name':'Jourdan', 'first_name':'Gil', 'birth_date':'1956-09-20'}
])
```

**Note**: half_orm works in autocommit mode by default. Without a transaction, any missing data
would be inserted.

### Returned values

By default `ho_insert` returns all the inserted values as a dictionary. You can specify the columns
you want to get by passing their names as argurments to `ho_insert`.

## ho_update

To update a subset, you first define the subset an then invoque the `ho_udpate`
method with the new values passed as argument.

```py
gaston = Person(first_name='Gaston')
gaston.ho_update(birth_date='1970-01-01')
```

Let's look at how we could turn the last name into capital letters for a subset of people:

```py
class Person(halftest.get_relation_class('actor.person')):
    # [...]

    def upper_last_name(self):
        "tranform last name to upper case."

        def update(self):
            for d_pers in self.ho_select('id', 'last_name'):
                pers = Person(**d_pers)
                pers.ho_update(last_name=d_pers['last_name'].upper())
        with Transaction(self._ho_model):
            update(self)
```

We here use the `Transaction` context manager to insure the atomicity of 
the operation.

```
>>> a_pers = Person(last_name=('ilike', '_a%'))
>>> print([elt.last_name for elt in list(a_pers.ho_select())])
>>> a_pers = Person(last_name=('ilike', '_a%'))
>>> print([elt['last_name'] for elt in a_pers.ho_select('last_name')])
['Lagaffe', 'Maltese', 'Talon']
>>> a_pers.upper_last_name()
>>> print([elt['last_name'] for elt in a_pers.ho_select('last_name')])
['LAGAFFE', 'MALTESE', 'TALON']
```

### Returning values

To return the updated values, you can add to `ho_update` the column names you want to get, or `*` if you want to get all the columns.

```py
>>> gaston.ho_update('*', birth_date='1970-01-01')
```

### Update all data in a table

If you want to update all the data in a relation, you must set the argument `update_all` to `True`. A `RuntimeError` is raised otherwise.

```py
Person().ho_update(birth_date='1970-01-01', update_all=True)
```

## ho_delete

The `ho_delete` method allows you to remove a set of elements from a table:

```py
gaston = Person(first_name='Gaston')
gaston.ho_delete()
```

To remove every tuples from a table, you must set the argument `delete_all` to `True`. A `RuntimeError` is raised otherwise.

```py
Person().ho_delete(delete_all=True)
if not Person().ho_is_empty():
    print('Weird! You should check your "on delete cascade".')
```
Well, there is not much left after this in the `actor.person` table.

### Returning values

As for `ho_update`, to return the deleted values, you can add to `ho_delete` the column names you want to get, or `*` if you want to get all the columns.

```py
>>> gaston.ho_delete('first_name', 'last_name', 'birth_date')
```

## ho_select
The `ho_select` method is a generator. It returns all the data of the relation that matches the constraint defined on the Relation object.
The data is returned in a list of `dict`s.

```py
>>> people = Person()
>>> print(list(people.ho_select()))
[{'id': 6753, 'first_name': 'Gaston', 'last_name': 'Lagaffe', 'birth_date': datetime.date(1957, 2, 28)}, {'id': 6754, 'first_name': 'Bibi', 'last_name': 'Fricotin', 'birth_date': datetime.date(1924, 10, 5)}, {'id': 6755, 'first_name': 'Corto', 'last_name': 'Maltese', 'birth_date': datetime.date(1975, 1, 7)}, {'id': 6756, 'first_name': 'Achile', 'last_name': 'Talon', 'birth_date': datetime.date(1963, 11, 7)}, {'id': 6757, 'first_name': 'Gil', 'last_name': 'Jourdan', 'birth_date': datetime.date(1956, 9, 20)}]
>>> print(list(people.ho_select('id', 'last_name')))
[{'id': 6753, 'last_name': 'Lagaffe'}, {'id': 6754, 'last_name': 'Fricotin'}, {'id': 6755, 'last_name': 'Maltese'}, {'id': 6756, 'last_name': 'Talon'}, {'id': 6757, 'last_name': 'Jourdan'}]
>>>
```

You can set a limit or an offset:
```py
>>> people.ho_offset(1).ho_limit(2)
>>> print(list(people)) # Relation objects are iterators. so ho_select is optional
[{'id': 6754, 'first_name': 'Bibi', 'last_name': 'Fricotin', 'birth_date': datetime.date(1924, 10, 5)}, {'id': 6755, 'first_name': 'Corto', 'last_name': 'Maltese', 'birth_date': datetime.date(1975, 1, 7)}]
```

You can also get a subset of the attributes by passing a list of columns names to `ho_select`:

```py
>>> print(list(people.ho_select('last_name')))
[{'last_name': 'Lagaffe'}, {'last_name': 'Fricotin'}]
```

**Note**: The offset and limit still apply.

### Select one: the `ho_get` method

The `ho_get` method returns an Relation object whose fields are populated with the values from the corresponding row in the database.
It raises an [ExpectedOneError](https://github.com/collorg/halfORM/blob/main/half_orm/relation_errors.py)
Exception if 0 or more than 1 rows match the intention. The returned object is a singleton (see below).

```py
gaston = Person(last_name='Lagaffe').ho_get()
```

is equivalent to

```py
lagaffe = Person(last_name='Lagaffe')
if lagaffe.ho_is_empty() or lagaffe.ho_count() > 1:
    raise ExcpetedOneError
gaston = Person(**next(lagaffe.ho_select()))
gaston._ho_is_singleton = True
```

You could use `ho_get` to retreive the `id` of the row:

```py
gaston_id = Person(last_name='Lagaffe').ho_get('id').id.value
```

### Is it a set? Is it an element of the set?

Let's go back to our definition of the class `Person`. We would like to write a property that
returns the full name of **a** person.

```py
class Person(halftest.get_relation_class('actor.person')):
    # [...]
    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'
```

As such, the `full_name` property wouldn't make much sense:

```py
lagaffe = Person(last_name='Lagaffe')
lagaffe.full_name # returns 'None Lagaffe'
```

In this case, you can use the `@singleton` decorator to ensure that the self object refers to one and only one element:

```py
from half_orm.relation import singleton

class Person(halftest.get_relation_class('actor.person')):
    @property
    @singleton
    def full_name(self):
        return f'{self.first_name} {self.last_name}'

gaston = Person(first_name='Gaston')
gaston.full_name # now returns 'Gaston Lagaffe'
```

If zero or more than one person in the `actor.person` table had *Gaston* as their first name, a `NotASingletonError` exception would be raised:

```
half_orm.relation_errors.NotASingletonError: Not a singleton. Got X tuples
```

### Forcing  `_ho_is_singleton` attribute. (*advanced*)

By forcing the attribute `_ho_is_singleton` of a Relation object to True, you can avoid some unnecessary `ho_get()` that a `@singleton` decorator would have triggered. Here is an example:

```py
class Person(halftest.get_relation_class('actor.person')):
    # [...]
    @singleton
    def do_something_else(self):
        "Needs self to be a singleton"
        ...

    def do_something(self):
        for elt in self.ho_select():
            pers = Person(**elt)
            pers._ho_is_singleton = True # You must be pretty sure of what you're doing here. See the warning and the explanation.
            pers.do_something_else() # Warning! do_something_else won't check that pers is indeed a singleton
```

**Warning!** By setting `_ho_is_singleton` value to `True`, you disable the check that `@singleton` would have made before executing `do_something_else`.
This example works for two reasons:

1. `ho_select` is called without argument ensuring that all columns are retreived from the database.
Note: Calling `ho_select` with columns corresponding to the primary key as arguments would also have worked;
2. The table `actor.person` has a primary key which makes it a set (ie. each element returned by select is
indeed a singleton).

## ho_count: cardinality of a set

**[BREAKING CHANGE]** From version 0.12 onward, the *`__len__`* method has been deprecated. It has been replaced by the `ho_count` method.

*The code `len(Person())` must be replaced by `Person().ho_count()`*.


You can get the number of elements in a relation with the `ho_count` method, as in `Person().ho_count()`.

### The `NULL` value

`half_orm` provides the `NULL` value:

```py
from half_orm.null import NULL

nobody = Person()
nobody.last_name.set(NULL)
assert nobody.ho_count() == 0 # last_name is part of the PK
[...]
```

The `None` value, unsets a constraint on a field:

```py
[...]
nobody.last_name.set(None)
assert nobody.ho_count() == Person().ho_count()
```

## Set operators

You can use the set operators to set more complex constraints on your relations:
- `&`, `|`, `^` and `-` for `and`, `or`, `xor` and `not`.
Take a look at [the algebra test file](https://github.com/collorg/halfORM/blob/main/test/relation/algebra_test.py).
- you can also use the `==`, `!=` and `in` operators to compare two sets.

```py
my_selection = Person(last_name=('ilike', '_a%')) | Person(first_name=('like', 'A%'))
```

`my_selection` represents the set of people whose second letter of the name is in `['a', 'A']` or whose first letter of the first name is an `A`.


# Working with foreign keys [WIP]

> This is a work in progress

A relational object integrates all the material necessary to process its foreign keys and the
foreign keys that point to this object. When you print the object, its representation ends
with the information about the foreign keys:

```
To use the foreign keys as direct attributes of the class, copy/paste the Fkeys below into
your code as a class attribute and replace the empty string key(s) with the alias(es) you
want to use. The aliases must be unique and different from any of the column names. Empty
string keys are ignored.

Fkeys = {
    [...]
}
```

Let's see an example with the `blog.post` relation:

```py
>>> class Post(halftest.get_relation_class('blog.post')):
...     pass
...
>>> Post()
```
```
Inherits: <class '__main__.Post'>

This class allows you to manipulate the data in the PG relation:
TABLE: "halftest":"blog"."post"
DESCRIPTION:
The table blog.post contains all the post
made by a person in the blogging system.
FIELDS:
- id:                (int4) NOT NULL
- title:             (text)
- content:           (text)
- author_first_name: (text)
- author_last_name:  (text)
- author_birth_date: (date)

PRIMARY KEY (id)
UNIQUE CONSTRAINT (title, content)
FOREIGN KEYS:
- _reverse_fkey_halftest_blog_comment_post_id: ("id")
 ↳ "halftest":"blog"."comment"(post_id)
- author: ("author_first_name", "author_last_name", "author_birth_date")
 ↳ "halftest":"actor"."person"(first_name, last_name, birth_date)

To use the foreign keys as direct attributes of the class, copy/paste the Fkeys below into
your code as a class attribute and replace the empty string key(s) with the alias(es) you
want to use. The aliases must be unique and different from any of the column names. Empty
string keys are ignored.

Fkeys = {
    '': '_reverse_fkey_halftest_blog_comment_post_id',
    '': 'author',
}
```

It has two foreign keys named `_reverse_fkey_halftest_blog_comment_post_id` and `author`:
* `author` is the foreign key that refrences an `actor.person` from the table `blog.post`.
* `_reverse_fkey_halftest_blog_comment_post_id` is the foreign key that references a `blog.post` from the table `blog.comment`. The foreign key is traversed in opposite direction (from `blog.post` to `blog.comment`).

We add the aliases of our foreign keys by defining the class attribute `Fkeys` :

```py
class Post(halftest.get_relation_class('blog.post')):
    Fkeys = {
        'comments_rfk': '_reverse_fkey_halftest_blog_comment_post_id',
        'author_fk': 'author'
    }
```

**Note**: By convention, we suffix by `_fk` the foreign keys and by `_rfk` the foreign keys traversed in reverse.
The plural in `comments_rfk` indicates that a post can be referenced by many comments.

A foreign key is a transitional object, so when you instanciate a FKey object,
you get the relation it points to. The original constraint is propagated through the foreign key.

Given a post defined by a `constraint`:

```py
a_post = Post(**constraint)
comments_on_a_post = a_post.comments_rfk()
author_of_a_post = a_post.author_fk()
```

You can also add a filter on a foreign key.

```py
comments_on_a_post_containing_simple = a_post.comment_rfk(content=('ilike', '%simple%'))
```

The Fkey class has the `set` method which allows you to constrain a foreign key with a Relation object.
To get the comments made by Gaston, we simply constraint the `author_fk` Fkey to reference the entry corresponding to Gaston in the actor.person table. To do so, we use the `Fkey.set()` method:

```py
gaston = Person(first_name='Gaston')
gaston_comments = Comment()
gaston_comments.author_fk.set(gaston)
print(list(gaston_comments.ho_select())
```
## Chaining foreign keys

**Important note**: Foreign key chaining will only work if the modules corresponding to the tables are ordered
according to the names of the tables in the package. See the `hop` command.

You can easily chain foreign keys. For example, if you want to get all the comments made by Gaston
on his own posts:

```py
gaston = {'last_name':'Lagaffe', 'first_name':'Gaston', 'birth_date':'1957-02-28'}
gaston_id = Person(**gaston).ho_get('id').id.value # we ensure that Gaston is a singleton
list(gaston
    .post_rfk(**gaston)
    .comment_rfk(author_id=gaston_id))
```

**Note**: the `blog.post` table declares a foreign key on `actor.person(first_name, last_name, birth_date)`
while the `blog.comment` table declares a foreign key on `actor.person(id)`.

## The *`ho_join`* method [deprecated]

From version 0.11 onward, the *`ho_join`* method has been deprecated. It was too messy and can easily be replaced using the foreign keys.

For example, the old code:

```py
lagaffe = Person(last_name='Lagaffe')
res = lagaffe.ho_join(
    (Comment(), 'comments', ['id', 'post_id']),
    (Post(), 'posts', 'id')
)
```

becomes:

```py
res = []
lagaffe = Person(last_name='Lagaffe')
for idx, pers in enumerate(lagaffe):
    res.append(pers)
    res[idx] = {}
    posts = Person(**pers).post_rfk()
    res[idx]['posts'] = list(posts.ho_select('id'))
    res[idx]['comments'] = list(posts.comment_rfk().ho_select('id', 'post_id'))
```

# PostgreSQL functions and stored procedures

`half_orm.model.Model` class provides two methods to deal with functions and stored procedures:
`execute_function` and `call_procedure`. You can
pass parameters as a list or a dictionary (for named parameters). The returned value of
`execute_function` is a list of `dict` like objects.

```py
from half_orm.model import Model
halftest = Model('halftest')

res = halftest.execute_function('schema.my_function', *args)
res = halftest.execute_function('schema.my_function', **kwargs) # for named parameters

half_test.call_procedure('schema.my_procedure', *args)
half_test.call_procedure('schema.my_procedure', **kwargs) # for named parameters
```

# Last: SQL queries

If you realy need to invoke a SQL query not managed by half_orm, use
the `Model.execute_query` method:

```py
from half_orm.model import Model
halftest = Model('halftest')
halftest.execute_query('select 1')
```

By the way, this is the code used in the `Model.ping` method that makes sure the connection is established and attempts a reconnection if it is not.

**WARING: SQL INJECTION RISK!**
This method calls the psycopg2 method
[cursor.execute](https://www.psycopg.org/docs/cursor.html?highlight=execute#cursor.execute).
Make sure you read the psycopg2 documentation on
[passing parameters to SQL queries](https://www.psycopg.org/docs/usage.html#query-parameters)
if you need to use `execute_query`.



That's it! You've learn pretty much everything there is to know about `half_orm`.

# Next: `hop`, the GitOps `half_orm` packager [WIP][alpha]

The [`hop`](https://github.com/collorg/halfORM/blob/main/doc/hop.md) command, directly provided in this package (from version 0.8.0rc1), allows you to:

* ***create*** a Python package corresponding to the model of your database;
* ***patch*** the model and the corresponding Python code;
* ***test*** your database model and your business code.

More at https://github.com/collorg/halfORM/blob/main/doc/hop.md

# Want to contribute?

Fork me on Github: https://github.com/collorg/halfORM
