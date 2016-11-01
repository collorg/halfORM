# half_orm

half_orm is a really simple ORM for PostgreSQL (9+) fully written in Python3.

half_orm only deals with the data manipulation part of the SQL language (SELECT, INSERT, UPDATE, DELETE) making it's usage quite trivial. All the data definition language part (CREATE TABLE/VIEW) has been left to SQL or whatever software used to define the structure of the database.

half_orm can produce complex JSON aggregations from any table/view with very simple YAML directives (nested aggregations are possible).

# Documentation

## The connection file
## Typical use case
- Easily request your data in JSON,
- ...

## The ```halftest``` database ([SQL code](test/sql/halftest.sql))

The ```halftest``` defines:
- three tables:
 - ```actor.person```
 - ```blog.post```
 - ```blog.comment```
- one view:
 - ```blog.view.post_comment```

To access the database, we need a config file ([test/halftest.ini](test/halftest.ini))

## API Examples (Everything you need to know to program with half_orm in five minutes)
Some scripts snippets to illustrate the current implementation of the API.
## The Model class:
The first thing you need is a model object to play with your database. Let us play with the ```halftest``` database:
```python
from half_orm.model import Model

halftest = Model(config_file='test/halftest.ini')
```
Two methods are available:
- ```desc``` to display the structure of the database or of a relation in the database.
- ```relation``` to instanciate a Relation object and play with this relation.

```python
halftest.desc()
halftest.desc("blog.comment")
```
Without argument, the ```desc``` method iterates over every *relational object* of the database and prints it's representation. The expression ```halftest.desc("blog.comment")``` displays only the representation of the ```blog.comment``` table as bellow:

```
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
person = halftest.relation("actor.person")
```
With a Relation object, you can use the following methods if it is of type ```Table```:
- ```insert```
- ```select```, ```to_json```, ```get``` and ```getone```
- ```update```
- ```delete```

If the type of the relation is ```View```, only the ```select```, ... methods can be used.
### Insert
To insert a tuple in the relation, just use the ```insert``` method as shown bellow:
```python
@person.Transaction
def insert_many(person):
    person(last_name='Lagaffe', first_name='Gaston', birth_date='1957-02-28').insert()
    person(last_name='Fricotin', first_name='Bibi', birth_date='1924-10-05').insert()
    person(last_name='Maltese', first_name='Corto', birth_date='1975-01-07').insert()
    person(last_name='Talon', first_name='Achile', birth_date='1963-11-07').insert()
    person(last_name='Jourdan', first_name='Gil', birth_date='1956-09-20').insert()

insert_many(person)
```
You can put a transaction on any function/method using the ```Relation.Transaction``` decorator.

Note: half_orm works in autocommit mode by default.

### Select
```Select``` is a generator. Without any argument, it returns all the datas in the relation in a list of dictionaries. You can easily filter to get any subset:
```python
person = person(last_name=('_a%', 'like'))
print(person.json())
```

```json
[{"birth_date": -405219600, "id": 37, "last_name": "Lagaffe", "first_name": "Gaston"},
  {"birth_date": 158281200, "id": 39, "last_name": "Maltese", "first_name": "Corto"},
  {"birth_date": -194144400, "id": 40, "last_name": "Talon", "first_name": "Achile"}]
```
You can also get a subset of the attributes:
```python
for dct in person(last_name=('_a%', 'like')).select('last_name'):
     print(dct)
```

```python
{'last_name': 'Lagaffe'}
{'last_name': 'Maltese'}
{'last_name': 'Talon'}

```


### Update
In this example, we upper case the last name of all the persons for which the second letter is an ```a```:

```python
@person.Transaction
def update_a(person):
    for pers in person(last_name=('_a%', 'like')).get():
        pers.update(last_name=pers.last_name.value.upper())

update_a(person)
```
Again, we insure the atomicity of the transaction using the ```Relation.Transaction``` decorator.

```python
print(person(last_name=('_A%', 'like')).json())
```

```json
[{"birth_date": -405219600, "id": 37, "last_name": "LAGAFFE", "first_name": "Gaston"},
  {"birth_date": 158281200, "id": 39, "last_name": "MALTESE", "first_name": "Corto"},
  {"birth_date": -194144400, "id": 40, "last_name": "TALON", "first_name": "Achile"}]
```

### Delete
We finally remove every inserted tuples. Notice that we use the ```delete_all``` argument with a ```True``` value. The ```delete``` would have been rejected otherwise:
```python
person().delete(delete_all=True)

print(person().json())
```
Well, there is not much left after this in the ```actor.person``` table.
```
[]
```
That's it! You've learn pretty much everything there is to know to begin to use half_orm for testing purpose only (**THIS PROJECT IS STILL PRE-ALPHA**).
## Interested?
Fork me on Github: https://github.com/collorg/half_orm
