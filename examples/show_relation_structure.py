#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from half_orm.model import Model

model = Model('halftest')
Person = model.get_relation_class('actor.person')
print(Person())