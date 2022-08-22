#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from random import randint
import psycopg2
import sys
from unittest import TestCase
from datetime import date

from ..init import halftest
from half_orm.field import Field

class Test(TestCase):
    def setUp(self):
        self.pers = halftest.Person()
        self.post = halftest.Post()
        self.today = halftest.today

    def test_not_set_field(self):
        pers = self.pers()
        fields_set = {elt.is_set() for elt in self.pers._fields.values()}
        self.assertTrue(fields_set, {False})

    def test_set_field(self):
        pers = self.pers(first_name='jojo')
        self.assertTrue(pers.first_name.is_set())

    def test_idem(self):
        pers = self.pers(first_name='jojo')
        self.assertEqual(isinstance(pers.first_name, Field), True)

    def test_fields_names(self):
        field_names = set(self.pers._fields.keys())
        print(field_names)
        self.assertEqual(
            field_names,
            {'id', 'first_name', 'last_name', 'birth_date'})

    def test_relation_ref(self):
        first_name = self.pers.first_name
        print(first_name.relation)
        self.assertEqual(id(first_name.relation), id(self.pers))
