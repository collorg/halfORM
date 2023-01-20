#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from half_orm.model import Model

model = Model('halftest')
Person = model.get_relation_class('actor.person')
person = Person()
print(person.keys())

@Person.HoTransaction
def failed_insert(Person):
    "shoud fail as we try to insert the same person twice"
    Person(last_name="test", first_name="test", birth_date='1970-01-01').ho_insert()
    Person(last_name="test", first_name="test", birth_date='1970-01-01').ho_insert()

try:
    failed_insert(Person)
except:
    assert len(person) == 0

