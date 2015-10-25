#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

import sys
from unittest import TestCase
from datetime import date

from ..init import halftest
from halfORM import relation_errors, model

class Test(TestCase):
    def tearDown(self):
        halftest.connection.autocommit = True
        self.pers().delete(last_name=('%', 'like'))

    def setUp(self):
        self.pers = halftest.relation("actor.person")
        self.post = halftest.relation("blog.post")

    def insertion_test(self):
        """Insertion test"""
        pers = self.pers
        halftest.connection.autocommit = False
        for i in range(26):
            last_name = 'n{}'.format(chr(ord('a') + i))
            first_name = 'p{}'.format(i)
            birth_date = date.today()
            self.pers.insert(
                last_name=last_name,
                first_name=first_name,
                birth_date=birth_date)
        halftest.connection.commit()
        halftest.connection.autocommit = True
        self.assertEqual(pers().count(), 26)

    def __update_test(self):
        pers = self.pers()
        count = pers.last_name.set('a%', 'like')
        pers.last_name.set('a%', 'like')
        self.assertEqual(pers.count(), 10)
        pers.update(last_name=pers.last_name.uppercase())
        self.assertEqual(pers.count(), 0)
        self.assertEqual(pers.count(last_name=('A%', 'like')), 10)

