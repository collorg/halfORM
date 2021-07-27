**THIS PROJECT IS IN ALPHA STAGE. I'm looking for testers/contributors.**

# halfORM: PostgreSQL to Python made easy

```half_orm``` maps an existing PostgreSQL database to Python objects with [inheritance as defined in PostgreSQL](https://www.postgresql.org/docs/current/static/tutorial-inheritance.html).
## Why half?
The SQL language is divided in two different parts:
- the data definition language part (DDL) to manipulate the structure of a database,
- the data manipulation language par (DML) used for selecting, inserting, deleting and updating data in a database.

```half_orm``` only deals with the DML part. Basically the `INSERT`, `SELECT`, `UPDATE` and `DELETE` commands. This makes ```half_orm``` easy to learn and use. In a way, ```half_orm``` is more a ```ROM```  (relation-object mapper) than an ```ORM```.

# Getting started

You have a PostgreSQL database ready at hand (not  in production of course this is alpha!!!)
## Install ```half_orm```

run ```pip install half_orm``` in a virtual environment.

Set the shell variable ```HALFORM_CONF_DIR```:

```sh
% mkdir ~/.half_orm
% export HALFORM_CONF_DIR=~/.half_orm
```

Create a connection file in the ```HALFORM_CONF_DIR``` containing the following information (with your values):

```ini
[database]
name = db_name
user = username
password = password
host = localhost
port = 5432
```

Your ready to go!
## Connect to the database

```py
>>> from half_orm.model import Model
>>> my_db = Model('my_database')
```

Where ```my_database``` is the name of a file located in the directory referenced by
the shell variable ```HALFORM_CONF_DIR``` if defined, by ```/etc/half_orm``` otherwise.


## Get a rapid description of the database structure

Once connected to the database, you can easily have an overview of its structure:

```py
print(my_db)
```

It displays as many lines as there are relations, views or materialized views in your
database. Each row has the form:

```
<relation type> <"schema name"."relation name">
```

Where ```relation type``` is one of `r`, `v`, `m`: 

* `r` for a relation,
* `v` for a view,
* `m` for a materialized view.

for instance (using the halftest database):

```
r "actor"."person"
r "blog"."comment"
r "blog"."event"
r "blog"."post"
v "blog.view"."post_comment"
```

## Get the class of a relation (the `Model.get_relation_class` method)

To work with a relation in your database, you must instanciate the class:

```python
Person = halftest.get_relation_class('actor.person')
```

To get a full description of the corresponding relation, print an instance of the class:

```python
>>> print(Person())
__RCLS: <class 'half_orm.relation.Table_HalftestActorPerson'>
This class allows you to manipulate the data in the PG relation:
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
- _reverse_fkey_halftest_blog_comment_author_id: ("id")
 ↳ "halftest"."blog"."comment"(author_id)
- _reverse_fkey_halftest_blog_event_author_first_name_author_last_name_author_birth_date: ("birth_date", "first_name", "last_name")
 ↳ "halftest"."blog"."event"(author_first_name, author_last_name, author_birth_date)
- _reverse_fkey_halftest_blog_post_author_first_name_author_last_name_author_birth_date: ("birth_date", "first_name", "last_name")
 ↳ "halftest"."blog"."post"(author_first_name, author_last_name, author_birth_date)```
```

All the above information is extracted from the database:

* description: the comment on the relationship if there is one,
* fields: the list of columns, their types and contraints
* foreign keys: the list of FKs if any. A `_reverse_*` FK is a FK made on the current relation.

## Constraining a relation

The first way to constrain a relation, is to put values on its columns.

```python
Person(last_name=('ilike', 'Lag%')
Person(last_name='Lagaffe', first_name='Gaston', birth_date='1957-02-28')
Person(birth_date='1957-02-28')
```

To manipulate the data, we will use four methods : ```insert```, ```select```, ```update```,```delete```.


## Insert
To insert a tuple in the relation, use the ```insert``` method as shown bellow:
```python
Person(last_name='Lagaffe', first_name='Gaston', birth_date='1957-02-28').insert()
```
You can put a transaction on any function using the ```Relation.Transaction``` decorator.

```python
persons = Person()

@persons.Transaction
def insert_many(persons, data):
    for person in data:
        persons(**person).insert()

insert_many(persons, data=[
  {'last_name':'Lagaffe', 'first_name':'Gaston', 'birth_date':'1957-02-28'},
    {'last_name':'Fricotin', 'first_name':'Bibi', 'birth_date':'1924-10-05'},
    {'last_name':'Maltese', 'first_name':'Corto', 'birth_date':'1975-01-07'},
    {'last_name':'Talon', 'first_name':'Achile', 'birth_date':'1963-11-07'},
    {'last_name':'Jourdan', 'first_name':'Gil', 'birth_date':'1956-09-20'}
])
```

Notice:
- half_orm works in autocommit mode by default.
- if "Lagaffe" was already inserted, none of the data would be
inserted by insert_many.

## Select
The ```select``` method is a generator. It returns all the data of the relation that match the constraint defined on the Relation object.
The data is returned in a list of dictionaries.

```python
>>> persons = Person()
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

You can set a limit or an offset:
```python
>>> persons.offset(2).limit(3)
```

To put a constraint on an object, you just have to pass the arguments corresponding to the names of the fields you want to constrain.
A constraint is an SQL one. By default, the
comparison operator is '=' but you can use any/some
[comparison operator](https://www.postgresql.org/docs/9.0/static/functions-comparison.html)
or [pattern matching operator (like or POSIX regular expression)](https://www.postgresql.org/docs/current/static/functions-matching.html)
 with a tuple of the form: ```(comp, value)```.

```python
>>> _a_persons = persons(last_name=('like',  '_a%'))
```

```python
>>> list(_a_persons.select())
[RealDictRow([('id', 144), ('first_name', 'Gaston'), ('last_name', 'Lagaffe'), ('birth_date', datetime.date(1957, 2, 28))]), RealDictRow([('id', 146), ('first_name', 'Corto'), ('last_name', 'Maltese'), ('birth_date', datetime.date(1975, 1, 7))]), RealDictRow([('id', 147), ('first_name', 'Achile'), ('last_name', 'Talon'), ('birth_date', datetime.date(1963, 11, 7))])]
```
You can also get a subset of the attributes:
```python
>>> for dct in _a_persons.select('last_name'):
...     print(dct)
{'last_name': 'Lagaffe'}
{'last_name': 'Maltese'}
{'last_name': 'Talon'}
```

## get
The ```get``` return returns one object of type Relation.
It raises an exception if 0 or more than 1 object match the intention.

## Update
In this example, we capitalize the last name of all people whose second letter is an ```a```.
We use the ```get``` method which returns a Relation object to which we can directly apply the update method:

```python
>>> @persons.Transaction
... def upper_a(persons):
...     for d_pers in persons.select():
...         pers = Person(**d_pers)
...         pers.update(last_name=d_pers['last_name'].upper())
...
>>> upper_a(_a_persons)
```

**WARNING!** The following code is perfectly legitimate, but it won't work. ```_a_persons.select()``` returns a list of dictionaries and the dict.update method would only update the corresponding dictonary. It's a common pitfall.

```python
>>> @persons.Transaction
... def upper_a(persons):
...     # Won't work!
...     for pers in persons.select():
...         # pers = Person(**d_pers)
...         pers.update(last_name=pers['last_name'].upper())
...
>>> upper_a(_a_persons)
```


Again, we insure the atomicity of the transaction using the ```Relation.Transaction``` decorator.

```python
>>> list(Person(last_name=('like', '_A%')).select())
[RealDictRow([('id', 144), ('first_name', 'Gaston'), ('last_name', 'LAGAFFE'), ('birth_date', datetime.date(1957, 2, 28))]), RealDictRow([('id', 146), ('first_name', 'Corto'), ('last_name', 'MALTESE'), ('birth_date', datetime.date(1975, 1, 7))]), RealDictRow([('id', 147), ('first_name', 'Achile'), ('last_name', 'TALON'), ('birth_date', datetime.date(1963, 11, 7))])]
```

If you want to update all the data in a relation, you must set the argument ```update_all``` to ```True```.

## Delete
We finally remove every inserted tuples. Notice that we use the ```delete_all``` argument with a ```True``` value. The ```delete``` would have been rejected otherwise:
```python
>>> persons().delete(delete_all=True)
>>> list(persons().select())
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
>>> Comment = halftest.get_relation_class('blog.comment')
>>> Comment()
__RCLS: <class 'half_orm.relation.Table_HalftestBlogComment'>
This class allows you to manipulate the data in the PG relation:
TABLE: "halftest"."blog"."comment"
DESCRIPTION:
The table blog.comment contains all the comments
made by a person on a post.
FIELDS:
- id:        (int4) PK
- content:   (text)
- post_id:   (int4)
- author_id: (int4)
- a = 1:     (text)
FOREIGN KEYS:
- post: ("post_id")
 ↳ "halftest"."blog"."post"(id)
- author: ("author_id")
 ↳ "halftest"."actor"."person"(id)
 ```

It has two foreign keys named ```post``` and ```author```.

We want the comments made by Gaston:

```python
>>> gaston = Person(last_name="Lagaffe")
>>> gaston_comments = Comment()
>>> gaston_comments._fkeys['author'].set(gaston)
```

To know on which posts gaston has made at least one comment, we just "call"
the foreign key ```post``` on ```gaston_comments```:

```python
>>> the_posts_commented_by_gaston = gaston_comments._fkeys['post']()
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
>>> the_authors_of_posts_commented_by_gaston = the_posts_commented_by_gaston._fkeys['author']()
```
It's that easy!

That's it! You've learn pretty much everything there is to know with half_orm.

# Interested?
Fork me on Github: https://github.com/collorg/halfORM, give some feedback, report issues.


# Notice

The ```hop``` command is no longer part of the ```half_orm``` package.

# Experimental

Not sure we will keep what's bellow.

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
## to_json
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

