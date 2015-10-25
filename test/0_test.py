#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from random import randint
from unittest import TestCase
from .init import halftest

class Test(TestCase):
    def reset(self):
        pass

    def setUp(self):
        self.pers = halftest.relation("public.personne")
        self.billet = halftest.relation("public.billet")

    def select_count_0_test(self):
        """database is empty"""
        self.assertEqual(self.pers.count(), 0)
        self.assertEqual(self.billet.count(), 0)
