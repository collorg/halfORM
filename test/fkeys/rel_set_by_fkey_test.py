#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from half_orm.hotest import HoTestCase
from unittest import skip
from uuid import uuid4

from ..init import halftest

class Test(HoTestCase):
    def setUp(self):
        self.pers = halftest.person_cls()
        self.post = halftest.post_cls()
        self.user = self.pers(**self.pers(last_name='xxx', first_name='yyy', birth_date='1970-01-01').ho_insert())
        self.user2 = self.pers(**self.pers(last_name='xxxxx', first_name='yyyyy', birth_date='1970-01-01').ho_insert())
    def tearDown(self):
        self.user.ho_delete()
        self.user2.ho_delete()

    def add_post_for_user(self, user, title):
        return self.post(**user.post_rfk(title=title, content='re coucou').ho_insert())

    def test_just_fkey_set(self):
        "it should pass"
        self.assertEqual(len(self.user.post_rfk()), 0)
        title = str(uuid4())
        self.add_post_for_user(self.user, title)
        self.assertEqual(len(self.user.post_rfk()), 1)
        self.assertEqual(next(self.post(title=title).author_fk())['last_name'], 'xxx')

    def test_just_fkey_set_delete(self):
        "it should pass"
        self.add_post_for_user(self.user, 'machin')
        self.add_post_for_user(self.user2, 'truc')
        self.assertEqual(len(self.user.post_rfk()), 1)
        self.assertEqual(len(self.user2.post_rfk()), 1)
        self.user.post_rfk().ho_delete()
        self.assertEqual(len(self.user.post_rfk()), 0)
        self.assertEqual(len(self.user2.post_rfk()), 1)
    