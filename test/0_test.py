#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from random import randint
from unittest import TestCase
from .init import halftest

class Test(TestCase):
    def reset(self):
        pass

    def setUp(self):
        self.pers = halftest.relation("actor.person")
        self.pers.delete(no_clause=True)
        self.post = halftest.relation("blog.post")
        self.post.delete(no_clause=True)

    def select_count_0_test(self):
        self.assertEqual(len(self.pers), 0)
        self.assertEqual(len(self.post), 0)
