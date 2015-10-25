#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

import sys
from unittest import TestCase
from ..init import halftest
from halfORM import relation_errors, model

class Test(TestCase):
    def reset(self):
        pass

    def setUp(self):
        self.pers = halftest.relation("blog.person")

    def unknown_field_test(self):
        """Unknonw field test"""
        with self.assertRaises(AttributeError) as cm:
            self.pers.unknown
        self.assertEqual(
            cm.exception.args[0],
            "'Table_HalftestBlogPerson' object has no attribute 'unknown'")
