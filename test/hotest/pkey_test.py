#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from half_orm.hotest import HoTestCase

from ..init import halftest

class Test(HoTestCase):
    def setUp(self):
        self.pers = halftest.person_cls()

    def test_pkey(self):
        "it should pass"
        self.hotAssertIsPkey(self.pers, ['first_name', 'last_name', 'birth_date'])

    def test_pkey_error(self):
        "it should raise an error"
        with self.assertRaises(AssertionError):
            self.hotAssertIsPkey(self.pers, ['id'])
