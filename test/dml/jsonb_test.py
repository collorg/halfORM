#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

import psycopg2
from unittest import TestCase

from ..init import halftest
from half_orm import relation_errors, model

class Test(TestCase):
    def setUp(self):
        self.post = halftest.Post()

    def tearDown(self):
        pass

    def test_jsonb(self):
        "should insert, update, delete jsonb in blog.post"
        title = 'title test_jsonb'
        self.post.title = title
        self.post._ho_mogrify()
        self.post.content = 'content test_jsonb'
        data = {'a': 'b'}
        self.post.data = data
        self.post._ho_insert()
        self.assertEqual(len(self.post), 1)
        self.assertEqual(next(self.post.select('data'))['data'], data)
        self.post = halftest.Post(title=title)
        ndata = {'a': 'c'}
        self.post._ho_update(data=ndata)
        self.post = halftest.Post(title=title, data=ndata)
        self.assertEqual(len(self.post), 1)
        self.post._ho_delete()
        self.assertEqual(len(self.post), 0)
