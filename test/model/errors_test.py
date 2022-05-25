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
