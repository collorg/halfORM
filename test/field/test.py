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
        self.pers = halftest.pers
        self.post = halftest.post
        self.today = halftest.today

    def not_set_field_test(self):
        pers = self.pers()
        fields_set = {elt.is_set() for elt in self.pers.fields}
        self.assertTrue(fields_set, {False})

    def set_field_test(self):
        pers = self.pers(first_name='jojo')
        self.assertTrue(pers._fields['first_name'].is_set())

    def idem_test(self):
        pers = self.pers(first_name='jojo')
        self.assertEqual(isinstance(pers._fields['first_name'], Field), True)

    def fields_names_test(self):
        field_names = {elt.name() for elt in self.pers.fields}
        print(field_names)
        self.assertEqual(
            field_names,
            {'id', 'first_name', 'last_name', 'birth_date'})

    def relation_ref_test(self):
        first_name = self.pers._fields['first_name']
        print(first_name.relation)
        self.assertEqual(id(first_name.relation), id(self.pers))

