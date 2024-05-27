#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from unittest import TestCase
from datetime import date

from half_orm.field import Field
from half_orm.null import NULL

from ..init import halftest

class Test(TestCase):
    def setUp(self):
        halftest.model.execute_query('create table test_neg(a int, b int, c text)')
        halftest.model.reconnect(reload=True)
        self.TestNeg = halftest.model.get_relation_class('public.test_neg')

    def tearDown(self):
        halftest.model.execute_query('drop table test_neg')
        halftest.model.reconnect(reload=True)

    def _test_neg(self):
        self.TestNeg(a=1, b=2, c='1').ho_insert()
        self.TestNeg(a=1, b=1).ho_insert()
        self.TestNeg(a=1, b=-1).ho_insert()
        test_neg = self.TestNeg()
        test_neg.a.set(-test_neg.b)
        test_neg.ho_mogrify()
        self.assertEqual(next(test_neg), {'a': 1, 'b': -1, 'c': None})

    def _test_neg_exception(self):
        self.TestNeg(a=1, b=2, c='1').ho_insert()
        test_neg = self.TestNeg()
        test_neg.a.set(test_neg.c)
        with self.assertRaises(ValueError) as exc:
            list(test_neg)
        self.assertEqual("Not a number!", str(exc.exception))
        