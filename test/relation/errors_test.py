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
        self.pers = halftest.relation("public.personne")

    def unknown_field_test(self):
        """Unknonw field test"""
        with self.assertRaises(AttributeError) as cm:
            self.pers.unknown
        self.assertEqual(
            cm.exception.args[0],
            "'Table_HalftestPublicPersonne' object has no attribute 'unknown'")
