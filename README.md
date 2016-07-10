# halfORM

halfORM is a really simple ORM (fully written in Python3), easy to learn (full documentation should be at most 10 pages) and hopefully less than a 1000 lines of Python3 code when it is done.

This project has just started (2015-10-18) and is in pre-alpha development stage. If you think you can contribute in any way, you are most welcome.

## Why half?
Because halfORM only deals with the data manipulation part of the SQL language (DML) making it much easier to learn and to write. All the CREATE part (data definition language) has been left to SQL or whatever software used to define the structure of the database.

## TODO
- Fix the API (**THIS PROJECT DEVELOPMENT STATE IS PRE-ALPHA**),
- doc doc doc and test test test,
- Port it to MySQL,
- Generate packages from the database,
- Generate a browsable graph of the database structure,
- PostgreSQL specific :
  - Deal with inheritance,

## Use cases
- Prototype in Python without investing too much in learning a complex ORM,
- You already have a PostgreSQL database and you want to see it's structure,
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

## API Examples (Everything you need to know to program with halfORM in five minutes)
Some scripts snippets to illustrate the current implementation of the API.
## The Model class:
The first thing you need is a model object to play with your database. Let us play with the ```halftest``` database:
```python
from halfORM.model import Model

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
- id:        (int4) PK
- content:   (text) 
- post_id:   (int4) 
- author_id: (int4) 
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
person = halftest.relation("actor.person")
```
With a Relation object, you can use the following methods if it is of type ```Table```:
- ```insert```
- ```select```, ```json```, ```get``` and ```getone```
- ```join```
- ```update```
- ```delete```

If the type of the relation is ```View```, only the ```select```, ```get``` and ```getone``` methods are present.
### Insert
To insert a tuple in the relation, just use the ```insert``` method as show bellow:
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

### Select/Json
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

### Playing with foreign keys
We want to see *Gaston*'s comments containing "m'enfin" on *Corto*'s posts.
```python
gaston = person(first_name="Gaston")
corto = person(first_name="Corto")
corto_post = halftest.relation("blog.post", author=corto)
gaston_comment_on_corto_post = halftest.relation(
    "blog.comment", text=("%m'enfin%", "ilike"), author=gaston, post=corto_post)
```

The representation of the request can be displayed just by printing the comment object:
```python
print(gaston_comment_on_corto_post)
```
```
TABLE: "halftest"."blog"."comment"
DESCRIPTION:
The table blog.comment contains all the comments
made by a person on a post.
FIELDS:
- id:        (int4) PK
- content:   (text)  (content ilike %m'enfin%)
- post_id:   (int4) 
- author_id: (int4) 
FOREIGN KEYS:
- post: (post_id)
  ↳ "halftest"."blog"."post"(id)
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
     FOREIGN KEY:
     - author: (author_first_name, author_last_name, author_birth_date)
       ↳ "halftest"."actor"."person"(first_name, last_name, birth_date)
          TABLE: "halftest"."actor"."person"
          DESCRIPTION:
          The table actor.person contains the persons of the blogging system.
          FIELDS:
          - id:         (int4) UNIQUE NOT NULL (id = 545)
          - first_name: (text) PK (first_name = Corto)
          - last_name:  (text) PK (last_name = MALTESE)
          - birth_date: (date) PK (birth_date = 1975-01-07)
- author: (author_id)
  ↳ "halftest"."actor"."person"(id)
     TABLE: "halftest"."actor"."person"
     DESCRIPTION:
     The table actor.person contains the persons of the blogging system.
     FIELDS:
     - id:         (int4) UNIQUE NOT NULL
     - first_name: (text) PK (first_name = Gaston)
     - last_name:  (text) PK
     - birth_date: (date) PK
```
### Join
The ```Relation.join``` method can be used to propagate constraints through relations:
```python
gaston_comment_on_corto_post = gaston.join(corto_post).join(comment)
```
The method can only join relations that are directly linked by foreign keys whatever the direction of the link is.
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
We finally remove every inserted tuples. Notice that we use the ```no_clause``` argument with a ```True``` value. The ```delete``` would have been rejected otherwise:
```python
person().delete(no_clause=True)

print(person().json())
```
Well, there is not much left after this in the ```actor.person``` table.
```
[]
```
That's it! You've learn pretty much everything there is to know to begin to use halfORM for testing purpose only (**THIS PROJECT IS STILL PRE-ALPHA**).
## Interested?
Fork me on Github: https://github.com/collorg/halfORM
