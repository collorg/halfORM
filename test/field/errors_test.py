#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from unittest import TestCase
from ..init import halftest
from half_orm import field_errors, model

conflict_msg = """'Field' object is not callable.
'last_name' is an attribute of type Field of the 'PC' object.
Do not use 'last_name' as a method name."""

class Test(TestCase):
    def reset(self):
        pass

    def setUp(self):
        self.pc = halftest.pc

    def test_conflict_name(self):
        msg = None
        with self.assertRaises(TypeError) as err:
            try:
                self.pc.last_name()
            except TypeError as terr:
                the_err = terr
                msg = str(terr)
                raise terr
        self.assertEqual(conflict_msg, msg)