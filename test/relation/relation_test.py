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

    def test_schemaname(self):
        "_schemaname should be 'actor' for the halftest.pers class"
        self.assertEqual(halftest.pers._schemaname, "actor")

    def test_tablename(self):
        "_relationname should be 'person' for the halftest.pers class"
        self.assertEqual(halftest.pers._relationname, "person")
