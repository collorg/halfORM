**THIS PROJECT IS IN ALPHA STAGE. I'm looking for testers/contributors to validate the API.**

# Welcome to halfORM, the PostgreSQL/Python3 relation/object mapper carefully designed to **NOT** address any of the data definition language part of SQL.

```half_orm``` is a really simple relational object mapper for PostgreSQL (9+) fully written in Python3. It manages the table inheritance of PostgreSQL and more...

## Why half?
The SQL language is divided in two different parts:
- the data definition language part (DDL) to manipulate the structure of a database,
- the data manipulation language par (DML) used for selecting, inserting, deleting and updating data in a database.

The half part of ```half_orm``` indicates that only the DML part is addressed. This makes ```half_orm``` learning and usage quite easy.

With ```half_orm``` you manipulate your data with true relational objects.

# Installation (only tested on Linux)
- Clone the project ```git clone https://github.com/collorg/halfORM```
- Install psycopg2 (http://initd.org/psycopg/docs/install.html)
- Go to the halfORM directory and install half_orm:
 ```sudo python3 setup.py -q install```. This will install the package and
 the script ```/usr/local/bin/halfORM```. The script can be used to generate
 a python package with all the relations of your database [WIP].

You're now ready to go!

# The full API

## The config file
Before we can begin, we need a configuration file to access the database. This file contains the database name, user name and password, host and port informations.
Keep it in a safe place. By default, ```half_orm``` looks for these files in
```/etc/half_orm``` directory.

Example: ([test/halftest.ini](test/halftest.ini))

## The ```halftest``` database ([SQL code](test/sql/halftest.sql))
The examples bellow use the [halftest example database](test/sql/halftest.sql).

The ```halftest``` has:
- for tables:
 - ```actor.person```
 - ```blog.post```
 - ```blog.event``` inherits ```blog.post```
 - ```blog.comment```
- one view:
 - ```blog.view.post_comment```

## API Examples (Everything you need to know to program with half_orm in 30 minutes)
Some scripts snippets to illustrate the current implementation of the API.
## The Model class:
The first thing you need is a model object to connect to your database.
```python
>>> from half_orm.model import Model
>>> halftest = Model(config_file='test/halftest.ini')
```
Four methods are available:
- ```desc``` to display the structure of the database or of a relation in the database.
- **```relation```**, the most important, to instanciate a Relation object and play with this relation. More on the ```Relation``` class below.
- ```ping``` to check if the connection is still up. It will attempt a reconnection if not. Very convenient to keep alive a web service even if the database
goes down.
- ```reconnect``` well, to reconnect and reload the metadata from the database possibly with another configuration file, allowing to change the role.

Without argument, the ```desc``` method iterates over every *relational object* of the database and prints it's type and name.

```python
>>> halftest.desc()
r "actor"."person"
r "blog"."comment"
r "blog"."post"
v "blog.view"."post_comment"
```

The expression ```halftest.desc("blog.comment")``` shows the representation of the ```blog.comment``` Relation:

```python
>>> halftest.desc("blog.comment")
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
Notice the two foreign keys on ```"halftest"."blog"."post"(id)``` and ```"halftest"."actor"."person"(id)```

## The Relation class:

To instanciate a Relation object, just use the ```Model.relation(QRN)``` method.
```QRN``` is the "qualified relation name" here ```actor.person```.
```python
>>> persons = halftest.relation("actor.person")
```
With a Relation object, you can use the following methods to manipulate the
data in your database:

If it is of type ```Table```:
- ```insert``` to insert data,
- ```select```, ```get```, ```getone``` and ```to_json``` to retreive data,
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

### get and getone
Like ```select```, ```get``` is a generator, but it returns a list Relation object.
These objects are of the same type of the object that invoqued the method.

```getone``` returns one object. It raises an exception if 0 or more than 1
ojects match the intention.

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
A Relational object has an attribute ```fkeys``` that contains the foreign
keys in a dictionary. Foreign keys are ```Fkey``` objects. The Fkey class
has one method:
- the ```set``` method allows you to constrain a foreign key with a Relation object,
- a foreign key is a transitional object, so when you "call" an FKey object,
you get the relation it points to. This relation is constrained by the
Relation object of origin.

Okay, let's see an example. Remember the ```blog.comment``` relation?

```python
>>> comments = halftest.relation("blog.comment")
>>> print(comments)
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
>>> gaston_comments.fkeys['author'].set(gaston)
```

To know on which posts gaston has made at least one comment, we just "call"
the foreign key ```post```:

```python
>>> the_posts = gaston_comments.fkeys['post']()
```
It's that easy!

# The halfORM script
Assuming you have a config file named ```halftest``` in ```/etc/half_orm```,
just run:
```sh
$ halfORM halftest
```
The script generates for you a package with a python module for each relation
in your database.
```sh
$ tree halftest/
halftest/
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
├── __init__.py
├── README.rst
└── setup.py
```

The modules are ordered by schema name (one directory by schema). The dot in
a schema name is used as a separator (```blog.view``` becomes ```blog/view```).
The classes in the relation modules are camel cased:
 - ```post```: ```Post```
 - ```post_comment```: ```PostComment```

 You can now edit those modules and use what you've learn.

To install the package, just go to the halftest directory and run:
```sh
python3 setup.py -q install
```

You can now write this script:

```python
#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from halform.blog.view.post_comment import PostComment

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
