#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from random import randint
import psycopg2
import sys
from unittest import TestCase
from datetime import date

from ..init import halftest
from halfORM import relation_errors, model

def name(letter, integer):
    return '{}{}'.format(letter, chr(ord('a') + integer))

class Test(TestCase):
    def setUp(self):
        self.today = date.today()
        self.pers = halftest.relation("actor.person")
        self.pers.delete(no_clause=True)
        self.post = halftest.relation("blog.post")
        self.pers.delete(no_clause=True)

        @self.pers.Transaction
        def insert_pers(pers):
            for n in 'abcdef':
                for i in range(10):
                    last_name = name(n, i)
                    first_name = name(n, i)
                    birth_date = self.today
                    self.pers(
                        last_name=last_name,
                        first_name=first_name,
                        birth_date=birth_date).insert()

        insert_pers(self.pers)

    def tearDown(self):
        self.pers().delete(last_name=('%', 'like'))
        self.assertEqual(len(self.pers()), 0)

    def count_test(self):
        self.assertEqual(len(self.pers()), 60)

    def expected_one_error_test_0(self):
        pers = self.pers(last_name="this name doesn't exist")
        self.assertRaises(
            relation_errors.ExpectedOneError, pers.getone)

    def expected_one_error_test_many(self):
        pers = self.pers(last_name=('%', 'like'))
        self.assertRaises(
            relation_errors.ExpectedOneError, pers.getone)

    def insert_error_test(self):
        pers = self.pers(last_name='ba')
        self.assertEqual(len(pers), 1)
        pers = pers.getone()
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
            self.pers(**dct).getone()

    def update_test(self):
        pers = self.pers(last_name=('a%', 'like'))
        self.assertEqual(len(pers), 10)
        pers.update(last_name=pers._fields['last_name'].value.upper())
        self.assertEqual(len(pers), 10)
