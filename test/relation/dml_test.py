#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from time import sleep
from random import randint
import psycopg2
import sys
from unittest import TestCase

from ..init import halftest
from half_orm import relation_errors, model

class Test(TestCase):
    def setUp(self):
        self.pers = halftest.pers
        self.post = halftest.post
        self.today = halftest.today

    def count_test(self):
        self.pers.mogrify()
        self.assertEqual(len(self.pers()), 60)

    def expected_one_error_test_0(self):
        pers = self.pers(last_name="this name doesn't exist")
        self.assertRaises(
            relation_errors.ExpectedOneError, pers.get)

    def expected_one_error_test_many(self):
        pers = self.pers(last_name=('%', 'like'))
        self.assertRaises(
            relation_errors.ExpectedOneError, pers.get)

    def insert_error_test(self):
        pers = self.pers(last_name='ba')
        self.assertEqual(len(pers), 1)
        pers = pers.get()
        self.assertRaises(psycopg2.IntegrityError, pers.insert)

    def select_test(self):
        n = 'abcdef'[randint(0, 5)]
        p = chr(ord('a') + range(10)[randint(0, 9)])
        pers = self.pers(
            last_name=('{}%'.format(n), 'ilike'),
            first_name=('%{}'.format(p), 'ilike'),
            birth_date=self.today)
        self.assertEqual(len(pers), 1)
        for dct in pers.select():
            self.pers(**dct).get()

    def update_test(self):
        pers = self.pers(last_name=('a%', 'like'))
        self.assertEqual(len(pers), 10)
        pers.update(last_name=pers.fields.last_name.value.upper())
        self.assertEqual(len(pers), 10)
