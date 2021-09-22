# A simple PostgreSQL-Python relation-object mapper.

```half_orm``` maps an existing PostgreSQL database to Python objects with [inheritance as defined in PostgreSQL](https://www.postgresql.org/docs/current/static/tutorial-inheritance.html).
## Why half?
The SQL language is divided in two different parts:
- the data definition language part ([DDL](https://www.postgresql.org/docs/13/ddl.html)) to manipulate the structure of a database,
- the data manipulation language part ([DML](https://www.postgresql.org/docs/13/dml.html)) used for selecting, inserting, deleting and updating data in a database.

```half_orm``` only deals with the DML part. Basically the `INSERT`, `SELECT`, `UPDATE` and `DELETE` commands. This makes ```half_orm``` easy to learn and use. In a way, ```half_orm``` is more a ```ROM```  (relation-object mapper) than an ```ORM```.

# Learn `half_orm` in half an hour

You have a PostgreSQL database ready at hand (you can try half_orm with [pagila](https://github.com/devrimgunduz/pagila))

## Install ```half_orm```

run ```pip install half_orm``` in a virtual environment.

Create a directory to store your connection files and set the shell variable ```HALFORM_CONF_DIR```:

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
>>> my_db = Model('my_database') # OK wrong naming... this is a Pg database ;)
```

The ```my_database``` is the name of the connexion file. It will be fetched in the directory referenced by
the shell variable ```HALFORM_CONF_DIR``` if defined, in ```/etc/half_orm``` otherwise.


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

Where ```relation type``` is one of `r`, `p`, `v`, `m`, `f`: 

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

## Check if a relation exists in the database

```py
>>> my_db.has_relation('blog.view.post_comment')
True
```

## Get the class of a relation (the `Model.get_relation_class` method)

To work with a table of your database, you must instanciate the corresponding class:

```python
Person = halftest.get_relation_class('actor.person')
PostComment = halftest.get_relation_class('blog.view.post_comment')
```

The argument passed to `get_relation_class` is as string of the form:
`<schema_name>.<relation_name>`. Note that while dots are allowed in the schemas, this is not the case for relations.

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

It provides you with information extracted from the database metadata:

* description: the comment on the relationship if there is one,
* fields: the list of columns, their types and contraints
* foreign keys: the list of FKs if any. A `_reverse_*` FK is a FK made on the current relation.


## Constraining a relation

when you instantiate an object with no arguments, its intention corresponds to all the data present in the corresponding relation.
```Person()``` represents the set of people contained in the ```actor.person``` table (ie. there is no constraint on the set). You can get the number of elements in a relation whith the ```len``` function as in ```len(Person())```.

To constrain a set, you must specify one or more values for the fields/columns in the set with a tuple of the form: ```(comp, value)```.
```comp``` (```=``` if ommited) is either a 
[comparison operator](https://www.postgresql.org/docs/13.0/static/functions-comparison.html) or a [pattern matching operator (like or POSIX regular expression)](https://www.postgresql.org/docs/current/static/functions-matching.html).

You can constrain a relation object at instanciation:

```python
Person(last_name='Lagaffe', first_name='Gaston', birth_date='1957-02-28')
Person(last_name=('ilike', '_a%'))
Person(birth_date='1957-02-28')
```

You can also constrain an instanciated object:

```py
gaston = Person()
gaston.last_name = ('ilike', 'l%')
gaston.first_name = 'Gaston'
```

`half_orm` prevents you from making typos:

```py
gaston.lost_name = 'Lagaffe'
# raises a half_orm.relation_errors.IsFrozenError Exception
```

### The `NULL` value

`half_orm` provides the `NULL` value:

```py
from half_orm.null import NULL

nobody = Person()
nobody.last_name = NULL
assert len(nobody) == 0 # last_name is part of the PK
```

## Set operators

You can use the set operators to set more complex constraints on your relations:
- ```&```, ```|```, ```^``` and ```-``` for ```and```, ```or```, ```xor``` and ```not```.
Take a look at [the algebra test file](https://github.com/collorg/halfORM/blob/master/test/relation/algebra_test.py).
- you can also use the ```==```, ```!=``` and ```in``` operators to compare two sets.

```python
my_selection = Person(last_name=('ilike', '_a%'))
my_selection |= Person(first_name=('ilike', 'A%'))
```

```my_selection``` represents the set of persons whose second letter of the name is an `a` or whose first letter of the first name is an `a`.


# DML. The ```insert```, ```select```, ```update```,```delete``` methods.

These methods trigger their corresponding SQL querie on the database. 
For debugging purposes, you can activate the print the SQL query built 
by half_orm when the DML method is invoked using the _mogrify() method.

```py
persons._mogrify()
persons.select()
```

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

```python
>>> _a_persons = Person(last_name=('like',  '_a%'))
```

```python
>>> [elt['last_name'] for elt in _a_persons.select()]
['Lagaffe', 'Maltese', 'Talon']
```

You can also get a subset of the attributes:

```python
>>> for dct in _a_persons.select('last_name'):
...     print(dct)
{'last_name': 'Lagaffe'}
{'last_name': 'Maltese'}
{'last_name': 'Talon'}
```

### Select one: the `get` method
the `get` method returns an object whose fields are constrained with the values of the corresponding row in the database.
It raises an [ExpectedOneError](https://github.com/collorg/halfORM/blob/master/half_orm/relation_errors.py)
Exception if 0 or more than 1 rows match the intention.

```py
gaston = Person(last_name='Lagaffe').get()
```

is equivalent to

```py
people = Person(last_name='Lagaffe')
if people.is_empty() or len(people) > 1:
    raise ExcpetedOneError
gaston = Person(**next(people.select()))
```

## Update

To update a subset, you first define the subset an then invoque the udpate
method with the new values passed as argument.

In the following example, we capitalize the last name of all people whose second letter is an ```a```.

```python
@persons.Transaction
def upper_a(persons):
    for d_pers in persons.select():
        pers = Person(id=d_pers['id'])
        pers.update(last_name=d_pers['last_name'].upper())

upper_a(_a_persons)
```

**WARNING!** The following code is perfectly legitimate, but it won't work. ```_a_persons.select()``` returns a list of dictionaries and the dict.update method would only update the corresponding dictonary. It's a common pitfall.

```python
@persons.Transaction
def upper_a(persons):
    # Won't work!
    for pers in persons.select():
        pers.update(last_name=pers['last_name'].upper())

upper_a(_a_persons)
```


Again, we insure the atomicity of the transaction using the ```Relation.Transaction``` decorator.

```python
>>> [elt['last_name'] for elt in Person(last_name=('like', '_A%')).select()]
['LAGAFFE', 'MALTESE', 'TALON']
```

If you want to update all the data in a relation, you must set the argument ```update_all``` to ```True```.

## Delete
We finally remove every inserted tuples. Note that we use the ```delete_all``` argument with a ```True``` value. The ```delete``` would have been rejected otherwise:
```python
>>> persons().delete(delete_all=True)
>>> list(persons().select())
[]
```
Well, there is not much left after this in the ```actor.person``` table.

# Working with foreign keys (the FKey class) and the *`join`* method

Working with foreign keys is as easy as working with Relational objects.
A Relational object has an attribute ```_fkeys``` that contains the foreign
keys in a dictionary. Foreign keys are ```Fkey``` objects. The Fkey class
has one method:
- the ```set``` method allows you to constrain a foreign key with a Relation object,
- a foreign key is a transitional object, so when you "call" an FKey object,
you get the relation it points to. The original constraint is propagated through the foreign key.

Let's see an example with the ```blog.comment``` relation:

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
gaston = Person(last_name="Lagaffe")
gaston_comments = Comment()
gaston_comments._fkeys['author'].set(gaston)
```

To know on which posts gaston made at least one comment, we just "call"
the foreign key ```post``` on ```gaston_comments```:

```python
>>> the_posts_commented_by_gaston = gaston_comments._fkeys['post']()
>>> isinstance(the_posts_commented_by_gaston, halftest.get_relation_class('blog.post'))
True
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
>>> list(the_authors_of_posts_commented_by_gaston.select())
[...]
```
Again, `the_authors_of_posts_commented_by_gaston` is an object of the class 
`halftest.get_relation_class('actor.person')`. It's that easy!

## the reverse Fkeys

With `half_orm` you can also go upstream.
If we look at the foreign keys of the `Person` class, they are
all prefixed by `_reverse_`. This means that the `actor.person`
table is referenced by other tables:

```py
FOREIGN KEYS:
- _reverse_fkey_halftest_blog_comment_author_id: ("id")
 ↳ "halftest"."blog"."comment"(author_id)
- _reverse_fkey_halftest_blog_event_author_first_name_author_last_name_author_birth_date: ("birth_date", "first_name", "last_name")
 ↳ "halftest"."blog"."event"(author_first_name, author_last_name, author_birth_date)
- _reverse_fkey_halftest_blog_post_author_first_name_author_last_name_author_birth_date: ("birth_date", "first_name", "last_name")
 ↳ "halftest"."blog"."post"(author_first_name, author_last_name, author_birth_date)
```

If we wanted to recover the `posts`, `events` and `comments` made by Gaston, we would just have to write:

```py
gaston = Person(last_name='Lagaffe', first_name='Gaston')
# assuming there is only one Gaston Lagaffe
g_comments = gaston._fkeys['_reverse_fkey_halftest_blog_comment_author_id']()
g_events = gaston._fkeys['_reverse_fkey_halftest_blog_event_author_first_name_author_last_name_author_birth_date']()
g_posts = gaston._fkeys['_reverse_fkey_halftest_blog_post_author_first_name_author_last_name_author_birth_date']()
```

## The *`join`* method

The *`join`* method allows to integrate the data associated to a Relation object in the result obtained by the *`select`* method.

Unlike the *`select`* method (which is a generator), it returns the data directly in a list.

The following code
```#python
lagaffe = Person(last_name='Lagaffe')
res = lagaffe.join(
    (Comment(), 'comments', ['id', 'post_id']),
    (Post(), 'posts', ['id'])
)
```
would return the list of people named `Lagaffe` with two
additional fields : `comments` and `posts`.

The data associated with `comments` is a list of dictionaries whose keys are 'id' and 'post_id'.
The data associated  with  `posts` is a simple list of values.

## Last: SQL queries

If you realy need to invoke a SQL query not managed by half_orm, use
the `Model.execute_query` method:

```py
from half_orm.model import Model
halftest = Model('halftest')
halftest.execute_query('select 1')
```

By the way, this is the code used in the `Model.ping` method that makes sure the connection is established and attempts a reconnection if it is not.

That's it! You've learn pretty much everything there is to know with `half_orm`.

# Next: `hop`, the `half_orm` packager

The [`hop`](https://github.com/collorg/halfORM_packager) command, provided by the package [`half_orm_packager`](https://github.com/collorg/halfORM_packager), allows you to ***create*** a Python package corresponding to the model of your database, to ***patch*** the model and the corresponding Python code, to ***test*** your database model and your business code. For more information, see https://github.com/collorg/halfORM_packager.

# Want to contribute?

Fork me on Github: https://github.com/collorg/halfORM

