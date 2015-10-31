#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import os.path
from halfORM.model import Model

dirname = os.path.dirname(__file__)
halftest = Model('{}/halftest.ini'.format(dirname))

corto = halftest.relation("actor.person", first_name="Corto")
post = halftest.relation("blog.post")
#post.title.value = 'Vaudou pour Monsieur le Président'
post.author.set(corto)
for p in post.select():
    print(p)
