#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

import psycopg2
from unittest import TestCase, skip

from ..init import halftest
from half_orm import relation_errors, model

class Test(TestCase):
    def setUp(self):
        self.pers = halftest.Person()
        self.post = halftest.Post()
        self.comment = halftest.Comment()
        aa = self.pers(last_name='aa')
        assert(len(aa) == 1)

    def tearDown(self):
        pass

    def test_post_fkeys_names(self):
        self.assertEqual(
            list(self.post._fkeys.keys()),
            ['_reverse_fkey_halftest_blog_comment_post_id', 'author'])

    def test_comment_fkeys_names(self):
        self.assertEqual(list(self.comment._fkeys.keys()), ['post', 'author'])

    def test_post_author_fkey_type(self):
        author = self.post.author_()
        self.assertTrue(isinstance(author, halftest.Person))

    def test_comment_author_fkey_type(self):
        author = self.comment.author_()
        self.assertTrue(isinstance(author, halftest.Person))

    def test_comment_post_fkey_type(self):
        post = self.comment._fkeys['post']()
        self.assertTrue(isinstance(post, halftest.Post))

    def test_is_set(self):
        post = self.post()
        self.assertFalse(post.ho_is_set())
        pers = self.pers(last_name=('a%', 'like'))
        post.author_.set(pers)
        self.assertTrue(post.ho_is_set())

    def test_is_not_set(self):
        post = self.post()
        self.assertFalse(post.ho_is_set())
        pers = self.pers()
        self.assertFalse(pers.ho_is_set())
        post.author_.set(pers)
        self.assertFalse(post.ho_is_set())

    def test_is_set_reverse(self):
        post = self.post(title="toto")
        author = post.author_()
        self.assertTrue(author.ho_is_set())

    def test_is_not_set_reverse(self):
        post = self.post()
        author = post.author_
        self.assertFalse(post.author_.is_set())
        self.assertFalse(post.author_().ho_is_set())

    def test_check_FKEYS_class(self):
        pers = self.pers()
        self.assertEqual(pers._post().__class__.__name__, self.post.__class__.__name__)
        self.assertEqual(pers._comment().__class__.__name__, self.comment.__class__.__name__)
        post = self.post()
        self.assertEqual(post.author_().__class__.__name__, self.pers.__class__.__name__)
        self.assertEqual(post.comment_fk().__class__.__name__, self.comment.__class__.__name__)

    @skip("Work in progress")
    def test_runtime_error(self):
        "should raise a RuntimeError exception"
        pers = self.pers()
        # A relation fkey attribute is a FKey class and the __set__ descriptor doesn't work on a class

        with self.assertRaises(RuntimeError) as err:
            print('pers._comment type', type(pers._comment), pers._comment)
            pers._comment = self.comment()
            # print(next(pers._ho_mogrify().ho_select()))
