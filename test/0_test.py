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
        self.post = halftest.relation("blog.post")

    def select_count_0_test(self):
        self.assertEqual(self.pers.count(), 0)
        self.assertEqual(self.post.count(), 0)
