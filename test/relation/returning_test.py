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
        halftest.Post()._ho_delete(delete_all=True)

    def test__ho_insert_returning_id(self):
        "should return blog.post id"
        self.post._ho_fkeys['author'].set(self.aa)
        self.post.title = 'test insert returning only id'
        self.post.content = ''
        d_res = self.post._ho_insert('id')
        self.assertEqual(list(d_res.keys()), ['id'])
        self.assertEqual(len(halftest.Post(**d_res)), 1)

    def test__ho_insert_returning_id_and_title(self):
        "should return columns id and title"
        self.post._ho_fkeys['author'].set(self.aa)
        self.post.title = 'test insert returning id and title'
        self.post.content = ''
        d_res = self.post._ho_insert('id', 'title')
        self.assertEqual(list(d_res.keys()), ['id', 'title'])
        self.assertEqual(len(halftest.Post(**d_res)), 1)

    def test__ho_insert_returning_all(self):
        "should return all columns"
        self.post._ho_fkeys['author'].set(self.aa)
        self.post.title = 'test insert returning all'
        self.post.content = ''
        d_res = self.post._ho_insert()
        self.assertEqual(set(d_res.keys()), set(halftest.Post()._ho_fields.keys()))
        self.assertEqual(len(halftest.Post(**d_res)), 1)

    def test__ho_delete_returns_none(self):
        "_ho_delete() should return None"
        self.post._ho_fkeys['author'].set(self.aa)
        self.post.title = 'test delete without returning values'
        self.post.content = ''
        d_res = self.post._ho_insert('id')
        self.assertEqual(len(halftest.Post(**d_res)), 1)
        self.assertEqual(halftest.Post(**d_res)._ho_delete(), None)
        self.assertEqual(len(halftest.Post(**d_res)), 0)

    def test__ho_delete_returning_id(self):
        "_ho_delete('id') should return a list of ids"
        self.post._ho_fkeys['author'].set(self.aa)
        self.post.title = 'test delete returning only id'
        self.post.content = ''
        d_res = self.post._ho_insert('id')
        self.assertEqual(len(halftest.Post(**d_res)), 1)
        self.assertEqual(halftest.Post(**d_res)._ho_delete('id'), [d_res])
        self.assertEqual(len(halftest.Post(**d_res)), 0)

    def test__ho_delete_returning_id_and_title(self):
        "_ho_delete('id') should return a list dicts {id, title}"
        self.post._ho_fkeys['author'].set(self.aa)
        self.post.title = 'test delete returning id and title'
        self.post.content = ''
        d_res = self.post._ho_insert('id', 'title')
        self.assertEqual(len(halftest.Post(**d_res)), 1)
        self.assertEqual(halftest.Post(**d_res)._ho_delete('id', 'title'), [d_res])
        self.assertEqual(len(halftest.Post(**d_res)), 0)

    def test__ho_delete_returning_all(self):
        "_ho_delete('id') should return a list of all values"
        self.post._ho_fkeys['author'].set(self.aa)
        self.post.title = 'test delete returning all'
        self.post.content = ''
        d_res = self.post._ho_insert('*')
        self.assertEqual(len(halftest.Post(**d_res)), 1)
        self.assertEqual(halftest.Post(**d_res)._ho_delete('*'), [d_res])
        self.assertEqual(len(halftest.Post(**d_res)), 0)

    def test__ho_update_returns_none(self):
        "_ho_update() should return None"
        self.post._ho_fkeys['author'].set(self.aa)
        self.post.title = 'test update without returning values'
        self.post.content = ''
        d_res = self.post._ho_insert('id', 'title')
        self.assertEqual(len(halftest.Post(**d_res)), 1)
        n_title = 'test update returning all after'
        self.assertEqual(halftest.Post(**d_res)._ho_update(title=n_title), None)
        self.assertEqual(len(halftest.Post(**d_res)), 0)

    def test__ho_update_returning_id(self):
        "_ho_update('id') should return a list of ids"
        self.post._ho_fkeys['author'].set(self.aa)
        self.post.title = 'test update with returning only id'
        self.post.content = ''
        d_res = self.post._ho_insert('id')
        self.assertEqual(len(halftest.Post(**d_res)), 1)
        n_title = 'test update returning id after'
        self.assertEqual(halftest.Post(**d_res)._ho_update('id', title=n_title), [d_res])
        d_res['title'] = n_title
        self.assertEqual(len(halftest.Post(**d_res)), 1)

    def test__ho_update_returning_id_and_title(self):
        "_ho_update('id') should return a list dicts {id, title}"
        self.post._ho_fkeys['author'].set(self.aa)
        self.post.title = 'test update with returning id and title'
        self.post.content = ''
        d_res = self.post._ho_insert('id', 'title')
        self.assertEqual(len(halftest.Post(**d_res)), 1)
        n_title = 'test update returning id and title after'
        n_d_res = dict(d_res)
        n_d_res['title'] = n_title
        self.assertEqual(halftest.Post(**d_res)._ho_update('id', 'title', title=n_title), [n_d_res])
        self.assertEqual(len(halftest.Post(**d_res)), 0)

    def test__ho_update_returning_all(self):
        "_ho_update('id') should return a list of all values"
        self.post._ho_fkeys['author'].set(self.aa)
        self.post.title = 'test update with returning all'
        self.post.content = ''
        d_res = self.post._ho_insert('*')
        self.assertEqual(len(halftest.Post(**d_res)), 1)
        n_title = 'test update returning all after'
        n_d_res = dict(d_res)
        n_d_res['title'] = n_title
        self.assertEqual(halftest.Post(**d_res)._ho_update('*', title=n_title), [n_d_res])
        self.assertEqual(len(halftest.Post(**d_res)), 0)
