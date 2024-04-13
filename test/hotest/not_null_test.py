#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from half_orm.hotest import HoTestCase

from ..init import halftest

class Test(HoTestCase):
    def setUp(self):
        self.pers = halftest.person_cls()
        self.post = halftest.post_cls()

    def test_not_null(self):
        "it should pass"
        self.hotAssertIsNotNull(self.pers, 'id')
        self.hotAssertIsNotNull(self.pers, 'first_name')

    def test_not_null_error(self):
        "it should raise an error"
        with self.assertRaises(AssertionError):
            self.hotAssertIsNotNull(self.post, 'content')
