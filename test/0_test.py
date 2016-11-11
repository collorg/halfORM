#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from random import randint
from unittest import TestCase
from .init import halftest

class Test(TestCase):
    def setUp(self):
        self.pers = halftest.pers
        self.post = halftest.post

    def select_count_0_test(self):
        self.pers.delete(delete_all=True)
        self.post.delete(delete_all=True)
        self.assertEqual(len(self.pers), 0)
        self.assertEqual(len(self.post), 0)
