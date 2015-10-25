# halfORM

halfORM is an attempt to make a really simple ORM (Python/PostgreSQL), easy to learn (full documentation must be at most 10 pages).

## Why half?
Because halfORM only deals with de data manipulation part of the SQL language. So all the CREATE part has been left to SQL or whatever software you use define the structure of your database.

## Use case
- You already have a PostgreSQL database and you want to see it's structure, extract some of your data in JSON, ...

## Example: The database
The following SQL code is the definition the halfORM test database ```halftest```.

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

Considering the config file ```test/halftest.ini```:
```
[database]
name = halftest
user = halftest
password = halftest
host = localhost
port = 5432
```
## Example: some scripts
The follwoing script instanciate a model object corresponding to the ```halftest``` database:
```python
from halfORM.model import Model

halftest = Model('test/halftest.ini')
halftest.desc()
```
It produces this output:
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
### Insert

```python
person = halftest.relation("actor.person")

person.insert(last_name='Lagaffe', first_name='Gaston', birth_date='1957-02-28')
person.insert(last_name='Fricotin', first_name='Bibi', birth_date='1924-10-05')
person.insert(last_name='Maltese', first_name='Corto', birth_date='1975-01-07')

print(person())
[{"first_name": "Gaston", "last_name": "Lagaffe", "birth_date": "1957-02-28"},
  {"first_name": "Bibi", "last_name": "Fricotin", "birth_date": "1924-10-05"},
  {"first_name": "Corto", "last_name": "Maltese", "birth_date": "1975-01-07"}]

person.insert(last_name='Talon', first_name='Achile', birth_date='1963-11-07')
person.insert(last_name='Jourdan', first_name='Gil', birth_date='1956-09-20')

print(person)
[{"first_name": "Gil", "last_name": "Jourdan", "birth_date": "1956-09-20"}]

print(person())
[{"first_name": "Gaston", "last_name": "Lagaffe", "birth_date": "1957-02-28"},
  {"first_name": "Bibi", "last_name": "Fricotin", "birth_date": "1924-10-05"},
  {"first_name": "Corto", "last_name": "Maltese", "birth_date": "1975-01-07"},
  {"first_name": "Achile", "last_name": "Talon", "birth_date": "1963-11-07"},
  {"first_name": "Gil", "last_name": "Jourdan", "birth_date": "1956-09-20"}]


```

### Select
```python
person = person(last_name=('_a%', 'like'))
print(person)
[{"last_name": "Lagaffe", "first_name": "Gaston", "birth_date": "1957-02-28"},
  {"last_name": "Maltese", "first_name": "Corto", "birth_date": "1975-01-07"},
  {"last_name": "Talon", "first_name": "Achile", "birth_date": "1963-11-07"}]
```

### Update
```python
halftest.connection.autocommit = False
for p in person.select(last_name=('_a%', 'like')):
    pers = person(**p)
    pers.update(last_name=p['last_name'].upper())
halftest.connection.commit()
print(person())
```

### Delete
```python
```
