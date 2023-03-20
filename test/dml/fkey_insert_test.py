#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

import psycopg2
from unittest import TestCase

from ..init import halftest
from half_orm import relation_errors, model

class Test(TestCase):
    def setUp(self):
        self.pers = halftest.Person()
        self.post = halftest.Post()
        self.comment = halftest.Comment()
        self.aa = self.pers(last_name='aa')
        assert(len(self.aa) == 1)

    def tearDown(self):
        pass

    def test_fkey_insert(self):
        "should insert blog.post with fkey reference on author"
        self.post._ho_fkeys['author'].set(self.aa)
        self.post.title = 'title test_direct_fkey_insert'
        self.post.content = 'content test_direct_fkey_insert'
        self.post._ho_insert()
        post = halftest.Post(title='title test_direct_fkey_insert')
        self.assertEqual(len(post), 1)
        self.post._ho_delete()
        self.assertEqual(len(post), 0)
