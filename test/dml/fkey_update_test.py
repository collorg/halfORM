#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

import psycopg2
from unittest import TestCase

from ..init import halftest
from half_orm import relation_errors, model

class Test(TestCase):
    def setUp(self):
        self.pers = halftest.person_cls()
        self.post = halftest.post_cls()
        self.comment = halftest.comment_cls()
        self.aa = self.pers(last_name='aa')
        assert(len(self.aa) == 1)

    def test_fkey_update(self):
        "should insert blog.post with fkey reference on author"
        self.post._ho_fkeys['author'].set(self.aa)
        self.post.title.set('title test_direct_fkey_insert')
        self.post.content.set('content test_direct_fkey_insert')
        self.post.ho_insert()
        post = halftest.post_cls(title='title test_direct_fkey_insert')
        self.assertEqual(len(post), 1)
        self.post.ho_update(title='title test_direct_fkey_insert updated')
        upost = halftest.post_cls(title='title test_direct_fkey_insert updated')
        self.assertEqual(len(post), 0)
        self.assertEqual(len(upost), 1)
        upost.ho_delete()
        self.assertEqual(len(post), 0)

