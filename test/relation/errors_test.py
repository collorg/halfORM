#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

import sys
from unittest import TestCase
from ..init import halftest
from half_orm import relation_errors, model

class Test(TestCase):
    def reset(self):
        pass

    def setUp(self):
        self.pers = halftest.pers

    def unknown_field_test(self):
        with self.assertRaises(AttributeError) as cm:
            self.pers.unknown
        self.assertEqual(
            cm.exception.args[0],
            "'Person' object has no attribute 'unknown'")
