#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import psycopg2
import sys
from halftest.actor.person import Person
from halftest.blog.comment import Comment


persons = Person() # instanciate a Person object without constraint
print(persons)
input("Hit return to continue ")

persons.delete(delete_all=True)
# as it is not constraint, delete_all=True must be provided to remove all
# the elements from 'actor.person' relation

# insert a person. All the pk attributes are set in kwargs
# Person.__init__ only accepts argument corresponding to the attributes of
# the relation in the PostgreSQL database.
gaston = persons(last_name='Lagaffe', first_name='Gaston', birth_date='1957-02-28')
print(gaston) # Note the constraint (all PK fields are set)
print("Before insert", len(gaston)) # No match in the database
gaston.insert()
print("After insert", len(gaston)) # Gaston is now in the database
input("continue ")

# insert many persons with a function. A transaction is put on the function
# with the decorator.
@persons.Transaction
def insert_many(persons, with_gaston=True):
    if with_gaston:
        persons(last_name='Lagaffe', first_name='Gaston', birth_date='1957-02-28').insert()
    persons(last_name='Fricotin', first_name='Bibi', birth_date='1924-10-05').insert()
    persons(last_name='Maltese', first_name='Corto', birth_date='1975-01-07').insert()
    persons(last_name='Talon', first_name='Achile', birth_date='1963-11-07').insert()
    persons(last_name='Jourdan', first_name='Gil', birth_date='1956-09-20').insert()

try:
    insert_many(persons) # Will fail as we attempt to add Gaston which is already present
except psycopg2.IntegrityError:
    pass
assert len(persons) == 1 # Only Gaston in the table
print("Still only one element", len(persons))
insert_many(persons, with_gaston=False) # The same without Gaston
assert len(persons) == 5
print("All elements have been inserted", len(persons))
input("continue ")

# Retreive data from the database using select:
for pers in persons.select():
    print(pers)
input("continue ")

# select_params to add parameters to the select [WIP]
persons.select_params(offset=2, limit=3)

for pers in persons.select():
    print(pers)
input("continue ")

# Puting a constraint using a comparison op. different than '='
_a_persons = persons(last_name=('_a%', 'like'))
print(_a_persons)

# getting the json representation of the select
_a_persons.to_json()
input("continue ")

# restricting to one attribute the result:
for dct in _a_persons.select('last_name'):
    print(dct)
input("continue ")

# using get to retreive the element in a Relation object (here a Person object)
gaston = persons(last_name="Lagaffe")
print(gaston)
gaston = gaston.get()
print(gaston)
input("continue ")

# get fails if 0 or more than one element match the request
try:
    persons.get() # all the elements in 'actor.person' (5 elements)
except Exception as err:
    print(err)
input("continue ")

# Foreign keys
comments = Comment()
gaston_comments = comments()
# Using obj._fkeys.<fkey_name>.set() to put a constraint on a Relation object
gaston_comments._fkeys.author.set(gaston)
print(gaston_comments)
input("continue ")

# Using  obj._fkeys.<fkey_name>() to get the Relation object pointed to
the_posts_commented_by_gaston = gaston_comments._fkeys.post()
print(the_posts_commented_by_gaston)
input("continue ")

# And again...
the_authors_of_posts_commented_by_gaston = the_posts_commented_by_gaston._fkeys.author()

# Using obj._mogrify() to display the SQL request
the_authors_of_posts_commented_by_gaston._mogrify()
input("continue ")

persons.delete(delete_all=True)
sys.exit()

# OLD CODE

import os.path
from half_orm.model import Model

dirname = os.path.dirname(__file__)
halftest = Model('{}/halftest.ini'.format(dirname))

person = halftest.relation("actor.person")
print(person)
person.delete(delete_all=True)
post = halftest.relation("blog.post")
print(post)
post.delete(delete_all=True)
comment = halftest.relation("blog.comment")
print(comment)
comment.delete(delete_all=True)

person = halftest.relation("actor.person")
print(type(person.last_name))
# just in case
#person.delete(delete_all=True)

@person.Transaction
def insert0(person):
    person(
        last_name='Lagaffe',
        first_name='Gaston',
        birth_date='1957-02-28').insert()
    person(
        last_name='Fricotin',
        first_name='Bibi',
        birth_date='1924-10-05').insert()
@person.Transaction
def insert1(person):
    insert0(person)
    person(
        last_name='Maltese',
        first_name='Corto',
        birth_date='1975-01-07').insert()
    person(
        last_name='Talon',
        first_name='Achile',
        birth_date='1963-11-07').insert()
def insert2(person):
    insert1(person)
    person(
        last_name='Jourdan',
        first_name='Gil',
        birth_date='1956-09-20').insert()
# TEST NESTED TRANSACTIONS
insert2(person)

print(person.json())
assert len(person) == 5

oo = person(first_name=('_o__o', 'like'))
print(oo)
assert len(oo) == 1

for p in person.get():
    assert len(p) == 1

_a = person(last_name=('_a%', 'like'))
a_count = len(_a)
print(_a.json())

@person.Transaction
def update(person):
    for pers in _a.get():
        pers.update(last_name=pers.last_name.value.upper())

update(person)

_A = person(last_name=('_A%', 'like'))
assert len(_A) == a_count

print(_A.json())

@person.Transaction
def update_rb(person):
    for pers in _A.get():
        print(pers.json())
        pers.update(first_name='A', last_name='A', birth_date='1970-01-01')

try:
    update_rb(person)
except Exception as err:
    pass

print(_A.json())

gaston = person(first_name="Gaston")
corto = person(first_name="Corto").getone()
corto_post = halftest.relation("blog.post", author=corto)
gaston_comment_on_corto_post = halftest.relation(
    "blog.comment",
    content=("%m'enfin%", "ilike"), author=gaston, post=corto_post)

print(gaston_comment_on_corto_post)
print('AVANT')
print("autocommit {}".format(gaston.model.connection.autocommit))
corto_post.select()
gaston_comment_on_corto_post.select()
print('APRÈS')

#person().delete(delete_all=True)

corto = halftest.relation("actor.person", first_name="Corto").getone()
post = halftest.relation("blog.post")
post.author = corto
post.title = 'Vaudou pour Monsieur le Président'
post.content = """Vaudou pour Monsieur le Président, qui se déroule à la Barbade (Antilles), puis sur l’île de Port-ducal (introuvable sur les cartes, mais que Pratt situe au sud-ouest de la Guadeloupe)."""
if len(post) == 0:
    post.insert()

post = post(title=('Vaudou%', 'like'))
#post.title.value = 'Vaudou pour Monsieur le Président'
post.author_fkey = corto
print(post)
post._mogrify()
