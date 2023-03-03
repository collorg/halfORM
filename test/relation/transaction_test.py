#!/usr/bin/env python
# -*- coding:  utf-8 -*-

from unittest import TestCase
from psycopg2.errors import UniqueViolation

from ..init import halftest


class Test(TestCase):
    def setUp(self):
        self.pers = halftest.Person()
        self.post = halftest.Post()
        self.today = halftest.today


    def test_transaction_rollback(self):
        "Should rollback with correct error"
        def error():
            @self.pers._ho_transaction
            def uniq_violation(pers):
                for name in ['abc', 'abd', 'aa']:
                    pers.__class__(
                        first_name=name, last_name=name, birth_date='1970-01-01')._ho_insert()

            uniq_violation(self.pers)

        self.assertRaises(UniqueViolation, error)
        self.assertEqual(60, len(self.pers))

    def test_transaction_rollback_to_level_0(self):
        "Should rollback to level 0 if nested transcation"
        def error():
            @self.pers._ho_transaction
            def uniq_violation2(pers):
                for name in ['xbc', 'xbd']:
                    pers.__class__(
                        first_name=name, last_name=name, birth_date='1970-01-01')._ho_insert()

            @self.pers._ho_transaction
            def uniq_violation1(pers):
                uniq_violation2(pers)
                for name in ['abc', 'abd', 'aa']:
                    pers.__class__(
                        first_name=name, last_name=name, birth_date='1970-01-01')._ho_insert()

            uniq_violation1(self.pers)

        self.assertRaises(UniqueViolation, error)
        self.assertEqual(self.pers._ho_transaction._Transaction__level, 0)