#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from half_orm.hotest import HoTestCase

from ..init import halftest

class Test(HoTestCase):
    def setUp(self):
        self.pers = halftest.person_cls()

    def test_unique(self):
        "it should pass"
        self.hotAssertIsUnique(self.pers, ['id'])
        self.hotAssertIsUnique(self.pers, ['first_name', 'last_name', 'birth_date'])

    def test_unique_error(self):
        "it should raise an error"
        with self.assertRaises(AssertionError):
            self.hotAssertIsUnique(self.pers, ['last_name'])
