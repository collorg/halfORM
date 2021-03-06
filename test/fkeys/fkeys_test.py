#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

import psycopg2
from unittest import TestCase

from ..init import halftest
from half_orm import relation_errors, model

class Test(TestCase):
    def setUp(self):
        self.pers = halftest.pers
        self.post = halftest.post
        self.comment = halftest.comment

    def post_fkeys_names_test(self):
        self.assertEqual(
            list(self.post._fkeys.keys()),
            ['_reverse_fkey_halftest_blog_comment_post_id', 'author'])

    def comment_fkeys_names_test(self):
        self.assertEqual(list(self.comment._fkeys.keys()), ['post', 'author'])

    def post_author_fkey_type_test(self):
        author = self.post.author_
        print(author.__class__, self.pers.__class__)
        self.assertTrue(isinstance(author, halftest.pers.__class__))

    def comment_author_fkey_type_test(self):
        author = self.comment.author_
        print(author.__class__, self.pers.__class__)
        self.assertTrue(isinstance(author, halftest.pers.__class__))

    def comment_post_fkey_type_test(self):
        post = self.comment._fkeys['post']()
        print(post.__class__, self.pers.__class__)
        self.assertTrue(isinstance(post, halftest.post.__class__))

    def is_set_test(self):
        post = self.post()
        self.assertFalse(post.is_set())
        pers = self.pers(last_name=('a%', 'like'))
        post.author_ = pers
        self.assertTrue(post.is_set())

    def is_not_set_test(self):
        post = self.post()
        self.assertFalse(post.is_set())
        pers = self.pers()
        self.assertFalse(pers.is_set())
        post.author_ = pers
        self.assertFalse(post.is_set())

    def is_set_reverse_test(self):
        post = self.post(title="toto")
        author = post.author_
        self.assertTrue(author.is_set())

    def is_not_set_reverse_test(self):
        post = self.post()
        author = post.author_
        self.assertFalse(author.is_set())

    def check_FKEYS_class_test(self):
        pers = self.pers()
        self.assertEqual(pers._post.__class__.__name__, self.post.__class__.__name__)
        self.assertEqual(pers._comment.__class__.__name__, self.comment.__class__.__name__)
        post = self.post()
        self.assertEqual(post.author_.__class__.__name__, self.pers.__class__.__name__)
        self.assertEqual(post.comment_fk.__class__.__name__, self.comment.__class__.__name__)