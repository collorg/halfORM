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

    def test_isinstance(self):
        pers = self.pers()
        self.assertTrue(isinstance(pers, self.pers.__class__))
