#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

import sys
from unittest import TestCase
from datetime import date

from ..init import halftest
from halfORM import relation_errors, model

class Test(TestCase):
    def setUp(self):
        self.pers = halftest.relation("actor.person")
        self.pers.delete(no_clause=True)
        self.post = halftest.relation("blog.post")
        self.pers.delete(no_clause=True)

    def tearDown(self):
        halftest.connection.autocommit = True
        self.pers().delete(last_name=('%', 'like'))

    def insertion_test(self):
        """Insertion test"""
        pers = self.pers
        halftest.connection.autocommit = False
        for i in range(26):
            last_name = 'n{}'.format(chr(ord('a') + i))
            first_name = 'p{}'.format(i)
            birth_date = date.today()
            self.pers(
                last_name=last_name,
                first_name=first_name,
                birth_date=birth_date).insert()
        halftest.connection.commit()
        halftest.connection.autocommit = True
        self.assertEqual(len(pers()), 26)

    def __update_test(self):
        pers = self.pers(last_name=('a%', 'like'))
        self.assertEqual(len(pers), 10)
        pers.update(last_name=pers.last_name.uppercase())
        self.assertEqual(len(pers), 0)
        self.assertEqual(len(pers(last_name=('A%', 'like'))), 10)

