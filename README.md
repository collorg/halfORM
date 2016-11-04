**Looking for testers/contributors**

**WARNING!** (2016-11-02)

```halfORM``` module has been renamed to ```half_orm```. If you were using halfORM and you want to upgrade to the lastest version:
- move ```/etc/halfORM``` directory to ```/etc/half_orm``` if you were using it,
- remove the installed module (```/usr/local/lib/python3.4/dist-packages/halfORM...``` on debian)
- change ```from halfORM.model import Model``` to ```from half_orm.model import Model``` in your scripts.

# What is half_orm?

```half_orm``` is a really simple ORM for PostgreSQL (9+) fully written in Python3.

## Why half?
The SQL language is divided in two different parts:
- DDL (Data definition language) to manipulate the structure of a database,
- DML (Data manipulation language) used for selecting, inserting, deleting and updating data in a database.

The half part of ```half_orm``` is here to indicate that only the data manipulation part of the SQL language is addressed. This makes ```half_orm``` learning and usage quite easy.
All the data definition language part has been left to SQL or whatever software used to define the structure of the database.

half_orm can produce complex JSON aggregations from any table/view with very simple YAML directives (nested aggregations are possible).

# Installation (only tested on Linux)
- Fork the project https://github.com/collorg/halfORM
- Install psycopg2 (http://initd.org/psycopg/docs/install.html)
- Go to the halfORM directory and install half_orm:
 ```sudo python3 setup.py -q install```


# The full API

## The config file
Before we can begin, we need a configuration file to access the database. This file contains the user name, database name, port
and host informations. By default, ```half_orm``` looks for these files in
```/etc/half_orm``` directory.

Example: ([test/halftest.ini](test/halftest.ini))

## The ```halftest``` database ([SQL code](test/sql/halftest.sql))
The examples bellow use the [halftest example database](test/sql/halftest.sql).

The ```halftest``` has:
- three tables:
 - ```actor.person```
 - ```blog.post```
 - ```blog.comment```
- one view:
 - ```blog.view.post_comment```

## API Examples (Everything you need to know to program with half_orm in five minutes)
Some scripts snippets to illustrate the current implementation of the API.
## The Model class:
The first thing you need is a model object to connect to your database.
```python
>>> from half_orm.model import Model
>>> halftest = Model(config_file='test/halftest.ini')
```
Four methods are available:
- ```desc``` to display the structure of the database or of a relation in the database.
- ```relation``` to instanciate a Relation object and play with this relation. More on the ```Relation``` class below.
- ```ping``` to check if the connection is still up. It will attempt a reconnection if not.
- ```reconnect``` well, to reconnect to the database.

Without argument, the ```desc``` method iterates over every *relational object* of the database and prints it's type and name.

```python
>>> halftest.desc()
r "actor"."person"
r "blog"."comment"
r "blog"."post"
v "blog.view"."post_comment"
```

The expression ```halftest.desc("blog.comment")``` displays only the representation of the ```blog.comment``` table as bellow:

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
- post_fkey: (post_id)
 ↳ "halftest"."blog"."post"(id)
- author_fkey: (author_id)
 ↳ "halftest"."actor"."person"(id)
```
Notice the two foreign keys on ```"halftest"."blog"."post"(id)``` and ```"halftest"."actor"."person"(id)```

## The Relation class:

To instanciate a Relation object, just use the ```Model.relation(QRN)``` method.
```QRN``` is the "qualified relation name" here ```actor.person```.
```python
>>> persons = halftest.relation("actor.person")
```
The persons object can be used to instanciate new ```actor.person``` objects.
With a Relation object, you can use the following methods to manipulate the
data in your database:

If it is of type ```Table```:
- ```insert```
- ```select```, ```to_json```, ```get``` and ```getone```
- ```update```
- ```delete```

If the type of the relation is ```View```, only the ```select```, ... methods can be used.

You also can use set operators to set complex constraints on your relations:
- ```&```, ```|```, ```^``` and ```-``` for ```and```, ```or```, ```xor``` and ```not```.
Take a look at [the algebra test file](test/relation/algebra_test.py).
- you can also use the ```==```, ```!=``` and ```in``` operators to compare two sets.
- you can finally get the number of elements in a relation whith ```len```.

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

Note: half_orm works in autocommit mode by default.

### Select
The ```select``` is a generator. It returns all the datas in the relation that match the constraint set on the Relation object.
The data are returned in a list of dictionaries.

Putting a constraint on a person object:
```python
>>> _a_persons = persons(last_name=('_a%', 'like'))
```
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

# Working with foreign keys
[WIP]


That's it! You've learn pretty much everything there is to know to begin to use half_orm for testing purpose only (**THIS PROJECT IS STILL PRE-ALPHA**).
## Interested?
Fork me on Github: https://github.com/collorg/halfORM
