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
        self.pers._ho_mogrify()
        self.assertEqual(len(self.pers()), 60)

    def test_expected_one_error_0(self):
        pers = self.pers(last_name="this name doesn't exist")
        self.assertRaises(
            relation_errors.ExpectedOneError, pers._ho_get)

    def test_expected_one_error_many(self):
        pers = self.pers(last_name=('like', '%'))
        self.assertRaises(
            relation_errors.ExpectedOneError, pers._ho_get)

    def test_insert_error(self):
        pers = self.pers(last_name='ba')
        self.assertEqual(len(pers), 1)
        pers = pers._ho_get()
        self.assertRaises(psycopg2.IntegrityError, pers._ho_insert)

    def test_select(self):
        n = 'abcdef'[randint(0, 5)]
        p = chr(ord('a') + range(10)[randint(0, 9)])
        pers = self.pers(
            last_name=('ilike', f'{n}%'),
            first_name=('ilike', f'%{p}'),
            birth_date=self.today)
        for dct in pers:
            self.pers(**dct)._ho_get()

    def test_select_from_dotted_schema(self):
        "should quote dotted schema in sql request"
        list(self.blog_view)

    def test_update(self):
        pers = self.pers(last_name=('like', 'a%'))
        self.assertEqual(len(pers), 10)
        @pers._ho_transaction
        def update(pers, fct):
            for elt in pers:
                pers = self.pers.__class__(**elt)
                pers._ho_update(last_name=fct(pers.last_name.value))
            
        update(pers, str.upper)
        pers = self.pers(last_name=('like', 'A%'))
        self.assertEqual(len(pers), 10)
        update(pers, str.lower)
