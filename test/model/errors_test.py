#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

import os
from unittest import TestCase
from ..init import halftest
from half_orm import model_errors, model



MISSING_SECTION_ERR=f"""Malformed config file: {os.environ['HALFORM_CONF_DIR']}/halftest_missing_database_section
Missing section: database"""
MISSING_MANDATORY_NAME=f"""Malformed config file: {os.environ['HALFORM_CONF_DIR']}/halftest_missing_mandatory_name
Missing mandatory parameter: name"""

class Test(TestCase):
    def tearDown(self):
        halftest.model.reconnect()

    def test_missing_config_file(self):
        self.assertRaises(
            model_errors.MissingConfigFile, model.Model, "missing")

    def test_malformed_config_file_missing_database_section(self):
        "it should raise MalformedConfigFile if database section is missing"
        with self.assertRaises(model_errors.MalformedConfigFile) as exc:
            halftest.model.reconnect('halftest_missing_database_section')
        self.assertEqual(str(exc.exception), MISSING_SECTION_ERR)

    def test_malformed_config_file_missing_mandatory_name(self):
        "it should raise MalformedConfigFile if mandatory parameter name is missing"
        with self.assertRaises(model_errors.MalformedConfigFile) as exc:
            halftest.model.reconnect('halftest_missing_mandatory_name')
        self.assertEqual(str(exc.exception), MISSING_MANDATORY_NAME)

    def test_missing_schema_in_name(self):
        "it should raise a MissingSchemaInName error"
        def bad_rel_name():
            halftest.model.get_relation_class('coucou')
        self.assertRaises(model_errors.MissingSchemaInName, bad_rel_name)

    def test_can_t_reconnect_to_another_database_error(self):
        "it should raise RuntimeError if we try to reconnect to another database"
        with self.assertRaises(RuntimeError) as exc:
            halftest.model.reconnect('halftest_other_name_error')
        self.assertEqual(
            str(exc.exception), "Can't reconnect to another database: another_db != halftest")

    def test_unknown_relation(self):
        "it should raise an UnknownRelation error"
        def unknown_rel():
            halftest.model.get_relation_class('public.coucou')
        self.assertRaises(model_errors.UnknownRelation, unknown_rel)
