#!/usr/bin/env python3
# -*- coding:  utf-8 -*-

from unittest import TestCase

from ..init import halftest, model, HALFTEST_STR, HALFTEST_REL_LISTS, HALFTEST_DESC


class Test(TestCase):
    def setUp(self):
        self.pg_meta = model._Model__pg_meta

    def test_desc(self):
        "it should return the list of relations as [(<type>, <fqrn>, [<inherits>, ...]), ...]"
        self.assertEqual(self.pg_meta.desc('halftest'), HALFTEST_DESC)

    def test_str(self):
        "it should return a well formatted string"
        self.maxDiff = None
        self.assertEqual(HALFTEST_STR, self.pg_meta.str('halftest'))

    def test_relations_list(self):
        self.maxDiff = None
        self.assertEqual(HALFTEST_REL_LISTS, self.pg_meta.relations_list('halftest'))
