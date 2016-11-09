#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from random import randint
import psycopg2
import sys
from unittest import TestCase
from datetime import date

from ..init import halftest
from half_orm import relation_errors, model

class Test(TestCase):
    def setUp(self):
        self.pers = halftest.relation("actor.person")
        self.post = halftest.relation("blog.post")

    def is_not_set_test(self):
        set_pers = self.pers(id=1)
        non_set_pers = set_pers()
        self.assertFalse(non_set_pers.is_set())

    def is_set_test(self):
        set_pers = self.pers(id=1)
        self.assertTrue(set_pers.is_set())

    def is_set_test_fkey(self):
        set_pers = self.pers(id=1)
        set_post = self.post()
        set_post._fkeys.author.set(set_pers)
        self.assertTrue(set_post.is_set())

    def is_set_test_op(self):
        non_set_pers = self.pers()
        set_pers = self.pers(id=1)
        non_set_pers |= set_pers()
        self.assertTrue(non_set_pers.is_set())

    def non_set_net_is_non_set_test(self):
        pers = self.pers()
        set_pers = -pers
        self.assertTrue(set_pers.is_set())
        self.assertFalse(pers.is_set())
