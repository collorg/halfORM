# halfORM (looking for contributors)

halfORM is an attempt to make a really simple ORM (fully written in Python3), easy to learn (full documentation should be at most 10 pages) and hopefully less than a 1000 lines of Python3 code when it is done.

This project has just started a week ago (2015-10-18) and I'd really like some contributors to help me out with it. So if you think you can contribute in any way, you are most welcome.

## Why half?
Because halfORM only deals with the data manipulation part of the SQL language (DML) making it much easier to learn and to write. All the CREATE part (data definition language) has been left to SQL or whatever software used to define the structure of the database.

## TODO
- Gather a community to develop this project,
- Fix the API (this project state is pre-alpha),
- doc doc doc and test test test,
- Port it to MySQL (I need someone with knowledge in MySQL),
- Add foreign key management,
- Generate packages from the database structure,
- Draw a navigational graph of the database structure,
- PostgreSQL specific :
  - Deal with inheritance,
  - Deal with FDW (not much to do here I suppose).

## Use cases
- Prototype in Python without investing too much in learning a complex ORM,
- You already have a PostgreSQL database and you want to see it's structure,
- Easily request your data in JSON,
- ...

## The ```halftest``` database ([SQL code](test/sql/halftest.sql))

The ```halftest``` defines:
- two schemas:
 - ```actor```
 - ```blog```
- three tables:
 - ```actor.person```
 - ```blog.post```
 - ```blog.comment``` 

To access the database, we need a config file ([test/halftest.ini](test/halftest.ini))

## API Examples
#### Some scripts snippets to illustrate the current implementation of the API.
The following script instanciate a model object corresponding to the ```halftest``` database:
```python
from halfORM.model import Model

halftest = Model(config_file='test/halftest.ini')
```
Let us look at the structure by using the ```desc``` method
```python
halftest.desc()
halftest.desc("blog.comment")
```
It iterates over every *relational object* of the database and prints it's representation. The expression ```halftest.desc("blog.comment")``` displays only the representation of the ```blog.comment``` table.

```
------------------------------------------------------------
TABLE: "halftest"."blog"."comment"
- cluster: halftest
- schema:  blog
- table:   comment
FIELDS:
- id:           (int4) PK
- content:      (text) 
- id_post:      (int4) 
- a_first_name: (text) 
- a_last_name:  (text) 
- a_birth_date: (date) 
FK post: (id)
   ↳ "halftest"."blog"."post"(id)
FK author: (first_name, last_name, birth_date)
   ↳ "halftest"."actor"."person"(first_name, last_name, birth_date)
```
Notice the two foreign keys on ```"halftest"."blog"."post"(id)``` and ```"halftest"."actor"."person"(first_name, last_name, birth_date)```

To instanciate a Relation object, just use the ```Model.relation(QRN)``` method.
```QRN``` is the "qualified relation name" here ```actor.person```.
```python
person = halftest.relation("actor.person")
```
With a Relation object, you can use 4 methods if it is of type ```Table```:
- ```insert```
- ```select```, ```get``` and ```getone```
- ```update```
- ```delete```

If the type of the relation is ```View```, only the ```select```, ```get``` and ```getone``` methods are present.
### Insert
To insert a tuple in the relation, just use the ```insert``` method as show bellow:
```python
person(last_name='Lagaffe', first_name='Gaston', birth_date='1957-02-28').insert()
person(last_name='Fricotin', first_name='Bibi', birth_date='1924-10-05').insert()
person(last_name='Maltese', first_name='Corto', birth_date='1975-01-07').insert()
person(last_name='Talon', first_name='Achile', birth_date='1963-11-07').insert()
person(last_name='Jourdan', first_name='Gil', birth_date='1956-09-20').insert()

print(person.json())
```

```json
[{"last_name": "Lagaffe", "first_name": "Gaston", "birth_date": -405219600},
  {"last_name": "Fricotin", "first_name": "Bibi", "birth_date": -1427673600},
  {"last_name": "Maltese", "first_name": "Corto", "birth_date": 158281200},
  {"last_name": "Talon", "first_name": "Achile", "birth_date": -194144400},
  {"last_name": "Jourdan", "first_name": "Gil", "birth_date": -419130000}]

```

### Select
You can easily filter to get any subset:
```python
person = person(last_name=('_a%', 'like'))
print(person.json())
```

```
[{"last_name": "Lagaffe", "first_name": "Gaston", "birth_date": -405219600},
  {"last_name": "Maltese", "first_name": "Corto", "birth_date": 158281200},
  {"last_name": "Talon", "first_name": "Achile", "birth_date": -194144400}]
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

#### Playing with foreign keys
We want to see *Gaston*'s comments containing "m'enfin" on *Corto*'s posts.
```python
gaston = person(first_name=("gaston", "ilike"))
corto = person(first_name=("corto", "ilike"))
corto_post = halftest.relation("blog.post", author=corto)
gaston_comment_on_corto_post = halftest.relation(
    "blog.comment", text=("%m'enfin%", "ilike"), author=gaston, post=corto_post)
```

The representation of the request can be displayed just by printing the comment object:
```python
print(gaston_comment_on_corto_post)
```
```
------------------------------------------------------------
Table: "halftest"."blog"."comment"
- cluster: halftest
- schema:  blog
- Table:   comment
FIELDS:
- id:           (int4) PK
- content:      (text)  (content ilike %m'enfin%)
- id_post:      (int4) 
- a_first_name: (text) 
- a_last_name:  (text) 
- a_birth_date: (date) 
FK post: (id)
   ↳ "halftest"."blog"."post"(id)
      ------------------------------------------------------------
      Table: "halftest"."blog"."post"
      - cluster: halftest
      - schema:  blog
      - Table:   post
      FIELDS:
      - id:           (int4) PK
      - title:        (text) 
      - content:      (text) 
      - a_first_name: (text) 
      - a_last_name:  (text) 
      - a_birth_date: (date) 
      FK author: (first_name, last_name, birth_date)
         ↳ "halftest"."actor"."person"(first_name, last_name, birth_date)
            ------------------------------------------------------------
            Table: "halftest"."actor"."person"
            - cluster: halftest
            - schema:  actor
            - Table:   person
            FIELDS:
            - first_name: (text) PK (first_name ilike corto)
            - last_name:  (text) PK
            - birth_date: (date) PK
FK author: (first_name, last_name, birth_date)
   ↳ "halftest"."actor"."person"(first_name, last_name, birth_date)
      ------------------------------------------------------------
      Table: "halftest"."actor"."person"
      - cluster: halftest
      - schema:  actor
      - Table:   person
      FIELDS:
      - first_name: (text) PK (first_name ilike gaston)
      - last_name:  (text) PK
      - birth_date: (date) PK
```

### Update
In this example, we upper case the last name all the persons in which the second letter is an ```a```:
```python
halftest.connection.autocommit = False
for dct in person(last_name=('_a%', 'like')).select():
    pers = person(**dct)
    pers.update(last_name=dct['last_name'].upper())
halftest.connection.commit()
halftest.connection.autocommit = False
```
To speed up things (not really necessary in this example), we turn ```autocommit``` to ```False``` before iterating over the tuples to update. We finally ```commit``` outside the for loop and turn ```autocommit``` back to ```False```.

Note: the ```Model.connection``` object is a ```psycopg2``` connection.

A better way to write this is by using the ```Relation.get``` method instead
of the ```select``` as it directly yields ```person``` type objects:

```python
halftest.connection.autocommit = False
for pers in person(last_name=('_a%', 'like')).get():
    pers.update(last_name=pers.last_name.value.upper())
halftest.connection.commit()
halftest.connection.autocommit = False
```

And finally, the ```Relation.transaction``` can be used to deal with transactions:

```python
@person.transaction
def update_a(person):
    for pers in person(last_name=('_a%', 'like')).get():
        pers.update(last_name=pers.last_name.value.upper())

update_a(person)
```

```python
print(person(last_name=('_A%*', 'like')).json())
```

```json
[{"birth_date": "1957-02-28", "first_name": "Gaston", "last_name": "LAGAFFE"},
  {"birth_date": "1975-01-07", "first_name": "Corto", "last_name": "MALTESE"},
  {"birth_date": "1963-11-07", "first_name": "Achile", "last_name": "TALON"}]
```

### Delete
We finally remove every inserted tuples. Notice that we use the ```no_clause``` argument with a ```True``` value. The ```delete``` would have been rejected otherwise:
```python
person().delete(no_clause=True)

print(person().json())
```
Well, there is not much left after this it the ```actor.person``` table.
```
[]
```
## Interested?
Fork me on Github: https://github.com/collorg/halfORM
