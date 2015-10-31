#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import os.path
from halfORM.model import Model

dirname = os.path.dirname(__file__)
halftest = Model('{}/halftest.ini'.format(dirname))

halftest.relation("actor.person").delete(no_clause=True)
halftest.relation("blog.post").delete(no_clause=True)
halftest.relation("blog.comment").delete(no_clause=True)
