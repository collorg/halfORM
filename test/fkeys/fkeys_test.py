#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

import psycopg2
from unittest import TestCase, skip

from ..init import halftest
from half_orm import relation_errors, model


ERR_MSG = """self.comment_rfk is not a FKey (got a Comment object instead).
- use: self.comment_rfk.set(Comment(...))
- not: self.comment_rfk = Comment(...)"""

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
            list(self.post._ho_fkeys.keys()),
            ['_reverse_fkey_halftest_blog_comment_post_id', 'author'])

    def test_comment_fkeys_names(self):
        self.assertEqual(list(self.comment._ho_fkeys.keys()), ['post', 'author'])

    def test_post_author_fkey_type(self):
        author = self.post.author_fk()
        self.assertTrue(isinstance(author, halftest.Person))

    def test_comment_author_fkey_type(self):
        author = self.comment.author_fk()
        self.assertTrue(isinstance(author, halftest.Person))

    def test_comment_post_fkey_type(self):
        post = self.comment._ho_fkeys['post']()
        self.assertTrue(isinstance(post, halftest.Post))

    def test_is_set(self):
        post = self.post()
        self.assertFalse(post.ho_is_set())
        pers = self.pers(last_name=('a%', 'like'))
        post.author_fk.set(pers)
        self.assertTrue(post.ho_is_set())

    def test_is_not_set(self):
        post = self.post()
        self.assertFalse(post.ho_is_set())
        pers = self.pers()
        self.assertFalse(pers.ho_is_set())
        post.author_fk.set(pers)
        self.assertFalse(post.ho_is_set())

    def test_is_set_reverse(self):
        post = self.post(title="toto")
        author = post.author_fk()
        self.assertTrue(author.ho_is_set())

    def test_is_not_set_reverse(self):
        post = self.post()
        author = post.author_fk
        self.assertFalse(post.author_fk.is_set())
        self.assertFalse(post.author_fk().ho_is_set())

    def test_check_FKEYS_class(self):
        pers = self.pers()
        self.assertEqual(pers.post_rfk().__class__.__name__, self.post.__class__.__name__)
        self.assertEqual(pers.comment_rfk().__class__.__name__, self.comment.__class__.__name__)
        post = self.post()
        self.assertEqual(post.author_fk().__class__.__name__, self.pers.__class__.__name__)
        self.assertEqual(post.comment_rfk().__class__.__name__, self.comment.__class__.__name__)

    def test_runtime_error(self):
        "should raise a RuntimeError exception"
        pers = self.pers()
        # A relation fkey attribute is a FKey class and the __set__ descriptor doesn't work on a class

        pers.comment_rfk = self.comment()
        err = None
        with self.assertRaises(RuntimeError) as err:
            list(pers.ho_select())
        self.assertEqual(str(err.exception), ERR_MSG)

    def test_expecting_a_relation_error(self):
        "it should raise an exception if we set with anything but a Relation object"
        with self.assertRaises(RuntimeError) as exc:
            self.pers().post_rfk.set('coucou')

    # def test_type_mismatch_error(self):
    #     "it should raise an exception if we set with a Relation "
    #     print(halftest.model)
    #     with self.assertRaises(RuntimeError) as exc:
    #         self.pers().post_rfk.set(self.view)
