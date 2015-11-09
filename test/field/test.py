#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from random import randint
import psycopg2
import sys
from unittest import TestCase
from datetime import date

from ..init import halftest
from halfORM.field import Field

class Test(TestCase):
    def setUp(self):
        self.today = date.today()
        self.pers = halftest.relation("actor.person")
        self.pers.delete(no_clause=True)
        self.post = halftest.relation("blog.post")
        self.pers.delete(no_clause=True)

    def tearDown(self):
        self.pers().delete(last_name=('%', 'like'))
        self.assertEqual(len(self.pers()), 0)

    def not_set_field_test(self):
        pers = self.pers()
        fields_set = {elt.is_set() for elt in self.pers.fields}
        self.assertTrue(fields_set, {False})

    def set_field_test(self):
        pers = self.pers()
        pers.first_name = 'jojo'
        self.assertTrue(pers.first_name.is_set())

    def idem_test(self):
        pers = self.pers()
        pers.first_name = 'jojo'
        self.assertEqual(isinstance(pers.first_name, Field), True)

    def fields_names_test(self):
        field_names = {elt.name() for elt in self.pers.fields}
        print(field_names)
        self.assertEqual(
            field_names,
            {'id', 'first_name', 'last_name', 'birth_date'})

    def relation_ref_test(self):
        first_name = self.pers.first_name
        print(first_name.relation)
        self.assertEqual(id(first_name.relation), id(self.pers))

