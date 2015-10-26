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

## Example: The ```halftest``` database
The following SQL code is the definition the halfORM test database ```halftest```. It defines:
- two schemas:
 - ```actor```
 - ```blog```
- three tables:
 - ```actor.person```
 - ```blog.post```
 - ```blog.comment``` 

### actor.person
```sql
create schema actor;
create table actor.person(
    first_name text,
    last_name text,
    birth_date date,
    primary key(first_name, last_name, birth_date)
);
```
### blog.post
```sql
create schema blog;
create sequence blog.id_post;
create table blog.post(
    id int default nextval('blog.id_post') unique not null,
    title text,
    content text,
    a_first_name text,
    a_last_name text,
    a_birth_date date,
    primary key(id)
);
alter table blog.post add constraint "author"
    foreign key(a_first_name, a_last_name, a_birth_date)
    references actor.person(first_name, last_name, birth_date)
	on update cascade on delete cascade;
```
## blog.comment
```sql
create sequence blog.id_comment;
create table blog.comment(
    id int default nextval('blog.id_comment') unique not null,
    content text,
    id_post int,
    a_first_name text,
    a_last_name text,
    a_birth_date date,
    primary key(id)
);
alter table blog.comment add constraint "author"
    foreign key(a_first_name, a_last_name, a_birth_date)
    references actor.person(first_name, last_name, birth_date)
	on update cascade on delete cascade;
alter table blog.comment add constraint "post"
    foreign key(id_post)
    references blog.post
	on update cascade on delete cascade;
```

To access the database, we have a config file, here ```test/halftest.ini```:
```
[database]
name = halftest
user = halftest
password = halftest
host = localhost
port = 5432
```
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
It iterates over every *relational object* of the database and prints it's representation. The expression ```halftest.desc("blog.comment")``` displays only the representation of the ```blog.comment``` table. Here is the output of ```halftest.desc()```:
```
------------------------------------------------------------
TABLE: "halftest"."actor"."person"
- cluster: halftest
- schema:  actor
- table:   person
FIELDS:
- first_name: (text) PK
- last_name:  (text) PK
- birth_date: (date) PK
```
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
```
------------------------------------------------------------
TABLE: "halftest"."blog"."post"
- cluster: halftest
- schema:  blog
- table:   post
FIELDS:
- id:           (int4) PK
- title:        (text) 
- content:      (text) 
- a_first_name: (text) 
- a_last_name:  (text) 
- a_birth_date: (date) 
FK author: (first_name, last_name, birth_date)
   ↳ "halftest"."actor"."person"(first_name, last_name, birth_date)
```
To instanciate a Relation object, just use the ```Model.relation(QRN)``` method.
```QRN``` is the "qualified relation name" here ```actor.person```.
```python
person = halftest.relation("actor.person")
```
With a Relation object, you can use 4 methods if it is of type ```Table```:
- ```insert```
- ```select```
- ```update```
- ```delete```

If the type of the relation is ```View```, only the ```select``` method is present.
### Insert
To insert a tuple in the relation, just use the ```insert``` method as show bellow:
```python
person.insert(last_name='Lagaffe', first_name='Gaston', birth_date='1957-02-28')
person.insert(last_name='Fricotin', first_name='Bibi', birth_date='1924-10-05')
person.insert(last_name='Maltese', first_name='Corto', birth_date='1975-01-07')
person.insert(last_name='Talon', first_name='Achile', birth_date='1963-11-07')
person.insert(last_name='Jourdan', first_name='Gil', birth_date='1956-09-20')

print(person)
```
Note that the intention is still attached to the person object and you only get the last inserted tuple:
```
[{"first_name": "Gil", "last_name": "Jourdan", "birth_date": "1956-09-20"}]
```
To get all the inserted persons, call a new person:
```python
print(person())
```

```
[{"first_name": "Gaston", "last_name": "Lagaffe", "birth_date": "1957-02-28"},
  {"first_name": "Bibi", "last_name": "Fricotin", "birth_date": "1924-10-05"},
  {"first_name": "Corto", "last_name": "Maltese", "birth_date": "1975-01-07"},
  {"first_name": "Achile", "last_name": "Talon", "birth_date": "1963-11-07"},
  {"first_name": "Gil", "last_name": "Jourdan", "birth_date": "1956-09-20"}]
```

### Select
You can easily filter to get any subset:
```python
person = person(last_name=('_a%', 'like'))
print(person)
```

```
[{"last_name": "Lagaffe", "first_name": "Gaston", "birth_date": "1957-02-28"},
  {"last_name": "Maltese", "first_name": "Corto", "birth_date": "1975-01-07"},
  {"last_name": "Talon", "first_name": "Achile", "birth_date": "1963-11-07"}]
```
You can also get a subset of the attributes:
```python
for dct in person.select('last_name', last_name=('_a%', 'like')):
     print(dct)
```

```
{'last_name': 'Lagaffe'}
{'last_name': 'Maltese'}
{'last_name': 'Talon'}

```

### Update
In this example, we upper case the last name all the persons in which the second letter is an ```a```:
```python
halftest.connection.autocommit = False
for dct in person.select(last_name=('_a%', 'like')):
    pers = person(**dct)
    pers.update(last_name=dct['last_name'].upper())
halftest.connection.commit()
halftest.connection.autocommit = False
```
To speed up things (not really necessary in this example), we turn ```autocommit``` to ```False``` before iterating over the tuples to update. We finally ```commit``` outside the for loop and turn ```autocommit``` back to ```False```.

Note: the ```Model.connection``` object is a ```psycopg2``` connection.

A better way to write this is by using the ```Relation.get``` method instead
of the ```select``` as it directly yields ```person``` objects:

```python
halftest.connection.autocommit = False
for pers in person().get(last_name=('_a%', 'like')):
    pers.update(last_name=pers.last_name.value.upper())
halftest.connection.commit()
halftest.connection.autocommit = False
```

```python
print(person(last_name=('_A%*', 'like')))
```

```
[{"birth_date": "1957-02-28", "first_name": "Gaston", "last_name": "LAGAFFE"},
  {"birth_date": "1975-01-07", "first_name": "Corto", "last_name": "MALTESE"},
  {"birth_date": "1963-11-07", "first_name": "Achile", "last_name": "TALON"}]
```


### Delete
We finally remove every inserted tuples. Notice that we use the ```no_clause``` argument with a ```True``` value. The ```delete``` would have been rejected otherwise:
```python
person().delete(no_clause=True)
print(person())
```
Well, there is not much left after this it the ```actor.person``` table.
```
[]
```
## Interested?
Fork me on Github: https://github.com/collorg/halfORM
