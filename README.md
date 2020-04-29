**THIS PROJECT IS IN ALPHA STAGE. I'm looking for testers/contributors to validate the API.**

# halfORM: PostgreSQL to Python made easy

```half_orm``` maps an existing PostgreSQL database to Python objects with [inheritance as defined in PostgreSQL](https://www.postgresql.org/docs/current/static/tutorial-inheritance.html).
## Why half?
The SQL language is divided in two different parts:
- the data definition language part (DDL) to manipulate the structure of a database,
- the data manipulation language par (DML) used for selecting, inserting, deleting and updating data in a database.

```half_orm``` only deals with the DML part. Basically the `INSERT`, `SELECT`, `UPDATE` and `DELETE` commands. This makes ```half_orm``` easy to learn and use.

# Getting started

## The config file
Before we can begin, we need a configuration file to access the database. This file contains the database name, user name and password, host and port informations. See the example: [test/halftest.ini](test/halftest.ini)
Keep it in a safe place. By default, ```half_orm``` looks for these files in
```/etc/half_orm``` directory.

## The ```halftest``` database ([SQL code](test/sql/halftest.sql))
The examples bellow use the [halftest example database](test/sql/halftest.sql).
To install the ```halftest``` database see [the installation instructions file](INSTALL.md).

### Connecting to the database (the Model class)
```python
#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from half_orm.model import Model

model = Model('halftest')
```

### Get a rapid description of the database structure (the `Model.desc` method)
```python
model.desc()
```
displays:
```
r "actor"."person"
r "blog"."comment"
r "blog"."event"
   inherits("blog"."post")
r "blog"."post"
v "blog.view"."post_comment"
```
`r` stands for relation, `v` for view. We can see that `blog.event` inherits from `blog.post`.

### Get the class of a relation/view (the `Model.get_relation_class` method)

```python
Person = model.get_relation_class('actor.person')
```
Just print an instance of the class to get a full description of the corresponding relation:
```python
print(Person())
```
displays:
```python
__RCLS: <class 'half_orm.relation.Table_HalftestActorPerson'>
This class allows you to manipulate the data in the PG relation/view:
TABLE: "halftest"."actor"."person"
DESCRIPTION:
The table actor.person contains the persons of the blogging system.
The id attribute is a serial. Just pass first_name, last_name and birth_date
to insert a new person.
FIELDS:
- id:         (int4) UNIQUE NOT NULL
- first_name: (text) PK
- last_name:  (text) PK
- birth_date: (date) PK
FOREIGN KEYS:
- _reverse_fkey_halftest_blog_comment_author_id: (id)
 ↳ "halftest"."blog"."comment"(author_id)
- _reverse_fkey_halftest_blog_event_author_first_name_author_last_name_author_birth_date: (last_name, birth_date, first_name)
 ↳ "halftest"."blog"."event"(author_first_name, author_last_name, author_birth_date)
- _reverse_fkey_halftest_blog_post_author_first_name_author_last_name_author_birth_date: (last_name, birth_date, first_name)
 ↳ "halftest"."blog"."post"(author_first_name, author_last_name, author_birth_date)
```

# The hop script

Assuming that you have copied [test/halftest.ini](test/halftest.ini) in ```/etc/half_orm/halftest``` and created the ```halftest``` database,
just run:
```sh
$ hop -c halftest -p halftest
```
The script generates for you a package with one python module for each relation
in your database. Install the package:

```sh
$ cd halftest
$ sudo -H pip3 install .
```

The structure of the Python package is:
```sh
$ $ tree -a halftest/
halftest/
├── .halfORM
│   └── config
├── halftest
│   ├── actor
│   │   ├── __init__.py
│   │   └── person.py
│   ├── blog
│   │   ├── comment.py
│   │   ├── event.py
│   │   ├── __init__.py
│   │   ├── post.py
│   │   └── view
│   │       ├── __init__.py
│   │       └── post_comment.py
│   ├── db_connector.py
│   └── __init__.py
├── README.rst
└── setup.py
```

The modules are organized by schema name (one directory per schema). The dot in
a schema name is used as a separator (```blog.view``` becomes ```blog/view```).
The classes in the relation modules are camel cased.

You now have acces to half_orm Relation classes matching the relations in your
database. The equivalence between PostgreSQL and Python is immediate:

| PostgreSQL relation (schemaname.relname) | module | class |
|----------|--------|-------|
| actor.person | halftest.actor.person | Person |
| blog.comment | haltest.blog.comment | Comment |
| blog.event | halftest.blog.event | Event |
| blog.post | halftest.blog.post | Post |
| "blog.view".post_comment | halftest.blog.view.post_comment | PostComment |

## The Relation class:

It provides the means to interact with the data in the database. Let us look
at the ```actor.person``` relation:
```python
>>> from halftest.actor.person import Person
```
You just have imported the Person class. The vocabulary used here is the one
that has been defined in your database. Let us instanciate a Person object
and print it:

```python
>>> persons = Person()
>>> persons
Init definition: Person(self, **kwargs)
Docstring:
TABLE: "halftest"."actor"."person"
DESCRIPTION:
The table actor.person contains the persons of the blogging system.
The id attribute is a serial. Just pass first_name, last_name and birth_date
to insert a new person.
FIELDS:
- id:         (int4) UNIQUE NOT NULL
- first_name: (text) PK
- last_name:  (text) PK
- birth_date: (date) PK
```
The structure of the relation is displayed as retreived from the database at
the time the ```hop``` command has been run. As the structure of your
database evolve, you can rerun the ```hop``` script whithout any argument
anywhere in the source of the package to keep in sync your modules.

With a Relation object, you can use the following methods to manipulate the
data in your database:

If it is of type ```Table```:
- ```insert``` to insert data,
- ```select```, ```get``` and ```to_json``` to retreive data,
  - ```select_params``` to set limit and/or offset,
- ```update``` to update data,
- ```delete``` to delete data.

You can "call" a Relation object to instanciate a new object with new constraints.

```python
new_rel = rel(**kwargs)
```

If the type of the relation is ```View```, only the ```select```, ... methods can be used.

You also can use set operators to set complex constraints on your relations:
- ```&```, ```|```, ```^``` and ```-``` for ```and```, ```or```, ```xor``` and ```not```.
Take a look at [the algebra test file](test/relation/algebra_test.py).
- you can also use the ```==```, ```!=``` and ```in``` operators to compare two sets.

You can get the number of elements in a relation whith ```len```.

Most of the snippets bellow are extracted from the example script: [test/halftest_doc.py](test/halftest_doc.py).

# Installation (tested on Linux/Mac OSX)
See [the installation instructions file](INSTALL.md).

# WORK IN PROGRESS

### Insert
To insert a tuple in the relation, just use the ```insert``` method as shown bellow:
```python
persons(last_name='Lagaffe', first_name='Gaston', birth_date='1957-02-28').insert()
```
You can put a transaction on any function/method using the ```Relation.Transaction``` decorator.
```python
@persons.Transaction
def insert_many(persons):
    persons(last_name='Lagaffe', first_name='Gaston', birth_date='1957-02-28').insert()
    persons(last_name='Fricotin', first_name='Bibi', birth_date='1924-10-05').insert()
    persons(last_name='Maltese', first_name='Corto', birth_date='1975-01-07').insert()
    persons(last_name='Talon', first_name='Achile', birth_date='1963-11-07').insert()
    persons(last_name='Jourdan', first_name='Gil', birth_date='1956-09-20').insert()

insert_many(persons)
```

Notice:
- half_orm works in autocommit mode by default.
- if "Lagaffe" was already inserted, none of the data would be
inserted by insert_many.

### Select
The ```select``` is a generator. It returns all the datas in the relation that match the constraint set on the Relation object.
The data are returned in a list of dictionaries.

```python
>>> for pers in persons.select():
...     print(pers)
...
{'first_name': 'Gaston', 'birth_date': datetime.date(1957, 2, 28), 'id': 159361, 'last_name': 'Lagaffe'}
{'first_name': 'Bibi', 'birth_date': datetime.date(1924, 10, 5), 'id': 159362, 'last_name': 'Fricotin'}
{'first_name': 'Corto', 'birth_date': datetime.date(1975, 1, 7), 'id': 159363, 'last_name': 'Maltese'}
{'first_name': 'Achile', 'birth_date': datetime.date(1963, 11, 7), 'id': 159364, 'last_name': 'Talon'}
{'first_name': 'Gil', 'birth_date': datetime.date(1956, 9, 20), 'id': 159365, 'last_name': 'Jourdan'}
>>>
```

You can limit of put and offset:
```python
>>> persons.select_params(offset=2, limit=3)
```

To put a constraint on a an object you just pass arguments corresponding to the
fields names you want to constrain. A constraint is an SQL one. By default, the
comparison operator is '=' but you can use any
[comparison operator](https://www.postgresql.org/docs/9.0/static/functions-comparison.html)
or [pattern matching operator (like or POSIX regular expression)](https://www.postgresql.org/docs/current/static/functions-matching.html)
 with a tuple of the form: ```(value, comp)```.

```python
>>> _a_persons = persons(last_name=('_a%', 'like'))
```

```python
>>> _a_persons.to_json()
'[{"first_name": "Gaston", "birth_date": "1957-02-28", "id": 159361, "last_name": "Lagaffe"},
 {"first_name": "Corto", "birth_date": "1975-01-07", "id": 159363, "last_name": "Maltese"},
 {"first_name": "Achile", "birth_date": "1963-11-07", "id": 159364, "last_name": "Talon"}]'
```
You can also get a subset of the attributes:
```python
>>> for dct in _a_persons.select('last_name'):
...     print(dct)
{'last_name': 'Lagaffe'}
{'last_name': 'Maltese'}
{'last_name': 'Talon'}
```

### get
The ```get``` return returns one object of type Relation.
It raises an exception if 0 or more than 1 object match the intention.

### to_json
the ```to_json``` method returns a json representation of the returned data.
It accepts a ```yml_directive``` that allows you to aggregate your data according
to your needs. For instance:

```python
yml_directive = """
authors:
   author_first_name: first_name
   author_last_name: last_name
   posts:
     - title: title
"""
post = halftest.relation('blog.post', last_name="Lagaffe")
post.to_json(yml_directive)
```
Would return the list of posts grouped by author. You can have more than one
level of aggregation.

```json
'[{"authors":[{"first_name": "Gaston", "last_name": "Lagaffe", "posts":[{"title": "Bof!"}, {"title": "Menfin!!!"}]}]}]'
```

In fact, this feature is very handy with SQL views. For example with the view
["blog.view".post_comment](test/sql/halftest.sql) you can get:

The list of posts with the comments on those posts
```yml
posts:
  - post_title: title
    author:
      author_post_first_name: first_name
      author_post_last_name: last_name
    comments:
      - comment_content: comment_content
        author:
          author_comment_first_name: first_name
          author_comment_last_name: last_name   
```

or the list of authors with their posts and the comments on thoses posts
```yml
authors:
  - author_post_first_name: first_name
    author_post_last_name: last_name
    posts:
      - post_title: title
        comments:
        - comment_content: content
          author:
            author_comment_last_name: last_name
            author_comment_first_name: first_name
```

### Update
In this example, we upper case the last name of all the persons for which the second letter is an ```a```.
We use the ```get``` method which returns a list of Relation objects:

```python
>>> @persons.Transaction
... def upper_a(persons):
...     for pers in persons.get():
...         pers.update(last_name=pers._fields['last_name'].value.upper())
...
>>> upper_a(_a_persons)
```
Again, we insure the atomicity of the transaction using the ```Relation.Transaction``` decorator.

```python
>>> persons(last_name=('_A%', 'like')).to_json()
'[{"first_name": "Gaston", "birth_date": "1957-02-28", "id": 159361, "last_name": "LAGAFFE"},
  {"first_name": "Corto", "birth_date": "1975-01-07", "id": 159363, "last_name": "MALTESE"},
  {"first_name": "Achile", "birth_date": "1963-11-07", "id": 159364, "last_name": "TALON"}]'
```

If you want to update all the data in a relation, you must set the argument ```update_all``` to ```True```.

### Delete
We finally remove every inserted tuples. Notice that we use the ```delete_all``` argument with a ```True``` value. The ```delete``` would have been rejected otherwise:
```python
>>> persons().delete(delete_all=True)
>>> persons().to_json()
[]
```
Well, there is not much left after this in the ```actor.person``` table.

# Working with foreign keys (the FKey class)
Working with foreign keys is as easy as working with Relational objects.
A Relational object has an attribute ```_fkeys``` that contains the foreign
keys in a dictionary. Foreign keys are ```Fkey``` objects. The Fkey class
has one method:
- the ```set``` method allows you to constrain a foreign key with a Relation object,
- a foreign key is a transitional object, so when you "call" an FKey object,
you get the relation it points to. This relation is constrained by the
Relation object of origin.

Okay, let's see an example. Remember the ```blog.comment``` relation?

```python
>>> from halftest.blog.comment import Comment
>>> comments = Comment()
>>> comments
TABLE: "halftest"."blog"."comment"
DESCRIPTION:
The table blog.comment contains all the comments
made by a person on a post.
FIELDS:
- author_id: (int4)
- id:        (int4) PK
- content:   (text)
- post_id:   (int4)
FOREIGN KEYS:
- post: (post_id)
 ↳ "halftest"."blog"."post"(id)
- author: (author_id)
 ↳ "halftest"."actor"."person"(id)
```

It has two foreign keys named ```post``` and ```author```.

We want the comments made by Gaston:

```python
>>> gaston = persons(last_name="Lagaffe")
>>> gaston_comments = comments()
>>> gaston_comments._fkeys.author.set(gaston)
```

To know on which posts gaston has made at least one comment, we just "call"
the foreign key ```post``` on ```gaston_comments```:

```python
>>> the_posts_commented_by_gaston = gaston_comments._fkeys.post()
```
Knowing that a Post object has the following structure:
```
TABLE: "halftest"."blog"."post"
DESCRIPTION:
The table blog.post contains all the post
made by a person in the blogging system.
FIELDS:
- id:                (int4) PK
- title:             (text)
- content:           (text)
- author_first_name: (text)
- author_last_name:  (text)
- author_birth_date: (date)
FOREIGN KEYS:
- author: (author_first_name, author_last_name, author_birth_date)
 ↳ "halftest"."actor"."person"(first_name, last_name, birth_date)
```
We can now retreive the authors of ```the_posts_commented_by_gaston```:
```python
>>> the_authors_of_posts_commented_by_gaston = the_posts_commented_by_gaston._fkeys.author()
```
It's that easy!

You can now write this script:

```python
#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from halform.db_connector import model
from halform.blog.view.post_comment import PostComment

model.reconnect('halftest_read_only_pc') # a role with only read rights

post_gaston = PostComment(author_post_first_name="Lagaffe")
posts_by_author = """
   ...: author:
   ...:   author_post_first_name: first_name
   ...:   author_post_last_name: last_name
   ...:   posts:
   ...:     - post_id: id
   ...:       post_title: title
   ...: """
post_gaston.to_json(posts_by_author)
```
That's it! You've learn pretty much everything there is to know with half_orm.
# Interested?
Fork me on Github: https://github.com/collorg/halfORM, give some feedback, report issues.
