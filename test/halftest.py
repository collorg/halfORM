#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import os.path
from halfORM.model import Model

dirname = os.path.dirname(__file__)
halftest = Model('{}/halftest.ini'.format(dirname))
person = halftest.relation("actor.person")

# just in case
person.delete(no_clause=True)

person.insert(last_name='Lagaffe', first_name='Gaston', birth_date='1957-02-28')
person.insert(last_name='Fricotin', first_name='Bibi', birth_date='1924-10-05')
person.insert(last_name='Maltese', first_name='Corto', birth_date='1975-01-07')
person.insert(last_name='Talon', first_name='Achile', birth_date='1963-11-07')
person.insert(last_name='Jourdan', first_name='Gil', birth_date='1956-09-20')

assert person.count() == 1
assert person().count() == 5

assert person(first_name=('_o__o', 'like')).count() == 1

for p in person.get():
    assert p.count() == 1

_a = person(last_name=('_a%', 'like'))
a_count = _a.count()

halftest.connection.autocommit = False
for pers in _a.get():
    pers.update(last_name=pers.last_name.value.upper())
halftest.connection.commit()
halftest.connection.autocommit = False

_A = person(last_name=('_A%', 'like'))
assert _A.count() == a_count

print(_A.json())

person().delete(no_clause=True)
