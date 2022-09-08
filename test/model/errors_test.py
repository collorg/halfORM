#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from unittest import TestCase
from ..init import halftest
from half_orm import model_errors, model

class Test(TestCase):
    def reset(self):
        pass

    def setUp(self):
        pass

    def test_missing_config_file(self):
        self.assertRaises(
            model_errors.MissingConfigFile, model.Model, "missing")

    def test_missing_schema_in_name(self):
        "it should raise a MissingSchemaInName error"
        def bad_rel_name():
            halftest.model.get_relation_class('coucou')
        self.assertRaises(model_errors.MissingSchemaInName, bad_rel_name)

    def test_unknown_relation(self):
        "it should raise an UnknownRelation error"
        def unknown_rel():
            halftest.model.get_relation_class('public.coucou')
        self.assertRaises(model_errors.UnknownRelation, unknown_rel)
