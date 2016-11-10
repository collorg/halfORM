#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

import psycopg2
from unittest import TestCase

from ..init import halftest

class Test(TestCase):
    def setUp(self):
        self.pers = halftest.pers()
        self.post = halftest.post()
        self.relation = halftest.relation

    def isinstance_test(self):
        pers = self.pers()
        print(pers.__class__, self.pers.__class__)
        print(id(pers.__class__), id(self.pers.__class__))
        self.assertTrue(isinstance(pers, self.pers.__class__))

    def isinstance_test_2(self):
        pers = self.relation('actor.person')
        print(pers.__class__, self.pers.__class__)
        print(id(pers.__class__), id(self.pers.__class__))
        self.assertTrue(isinstance(pers, self.pers.__class__))

