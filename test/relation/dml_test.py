#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from time import sleep
from random import randint
import psycopg2
import sys
from unittest import TestCase
from half_orm.hotest import HoTestCase

from ..init import halftest
from half_orm import relation_errors, model

class Test(HoTestCase):
    def setUp(self):
        self.pers = halftest.Person()
        self.post = halftest.Post()
        self.today = halftest.today
        self.blog_view = halftest.Blog_view()

    def test_count(self):
        self.pers._mogrify()
        self.assertEqual(len(self.pers()), 60)

    def test_expected_one_error_0(self):
        pers = self.pers(last_name="this name doesn't exist")
        self.assertRaises(
            relation_errors.ExpectedOneError, pers.get)

    def test_expected_one_error_many(self):
        pers = self.pers(last_name=('like', '%'))
        self.assertRaises(
            relation_errors.ExpectedOneError, pers.get)

    def test_insert_error(self):
        pers = self.pers(last_name='ba')
        self.assertEqual(len(pers), 1)
        pers = pers.get()
        self.assertRaises(psycopg2.IntegrityError, pers.insert)

    def test_select(self):
        n = 'abcdef'[randint(0, 5)]
        p = chr(ord('a') + range(10)[randint(0, 9)])
        pers = self.pers(
            last_name=('ilike', f'{n}%'),
            first_name=('ilike', f'%{p}'),
            birth_date=self.today)
        for dct in pers.select():
            self.pers(**dct).get()

    def test_select_from_dotted_schema(self):
        "should quote dotted schema in sql request"
        self.blog_view.select()

    def test_update(self):
        pers = self.pers(last_name=('like', 'a%'))
        self.assertEqual(len(pers), 10)
        @pers.Transaction
        def update(pers, fct):
            for elt in pers.select():
                pers = self.pers.__class__(**elt)
                pers.update(last_name=fct(pers.last_name.value))
            
        update(pers, str.upper)
        pers = self.pers(last_name=('like', 'A%'))
        self.assertEqual(len(pers), 10)
        update(pers, str.lower)
