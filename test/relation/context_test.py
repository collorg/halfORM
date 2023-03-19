#!/usr/bin/env python
#-*- coding:  utf-8 -*-

import sys
from unittest import TestCase
from random import randint
from datetime import date

import psycopg2
# from psycopg2.errors import UniqueViolation
from half_orm.transaction import Transaction

from ..init import halftest, GASTON

class Test(TestCase):
    def setUp(self):
        self.gaston = halftest.gaston
        self.gaston._ho_insert()
        self.ab = halftest.Person(last_name='a', first_name='b', birth_date='0001-01-01')
        self.post = halftest.Post()

    def tearDown(self):
        self.gaston._ho_delete()
        self.ab._ho_delete()
        pass

    def test_context(self):
        "context shout put the model in transaction mode"
        self.assertFalse(self.gaston._ho_transaction.is_set())
        with self.assertRaises(psycopg2.errors.UniqueViolation):
            with self.gaston as gaston:
                self.ab._ho_insert()
                self.assertTrue(self.gaston._ho_transaction.is_set())
                gaston._ho_insert()
        self.assertEqual(len(self.ab), 0)
        self.assertFalse(self.gaston._ho_transaction.is_set())
