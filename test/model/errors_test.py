#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from unittest import TestCase
from ..init import halftest
from halfORM import model_errors, model

class Test(TestCase):
    def reset(self):
        pass

    def setUp(self):
        pass

    def missing_config_file_test(self):
        """Missing config file test."""
        self.assertRaises(
            model_errors.MissingConfigFile, model.Model, "missing")

    def unknown_relation_test(self):
        """Unknown relation test."""
        self.assertRaises(
            model_errors.UnknownRelation, halftest.relation, "public.unknown")



