#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from half_orm.hotest import HoTestCase

from ..init import halftest

class Test(HoTestCase):
    def setUp(self):
        self.pers = halftest.Person()
        self.post = halftest.Post()

    def test_references(self):
        "it should pass"
        self.hotAssertReferences(self.post, 'author', halftest.Person)
        self.hotAssertReferences(self.post, '_reverse_fkey_halftest_blog_comment_post_id', halftest.Comment)

    def test_references_error(self):
        "it should raise an error"
        with self.assertRaises(AssertionError) as exc:
            self.hotAssertReferences(self.post, 'author', halftest.Comment)
        self.assertEqual(str(exc.exception), "Post()._ho_fkeys['author']() does not reference Comment")

    def test_alias_references(self):
        "it should pass"
        self.hotAssertAliasReferences(self.post, 'author_fk', halftest.Person)
        self.hotAssertAliasReferences(self.post, 'comment_rfk', halftest.Comment)

    def test_alias_references_error(self):
        "it should raise an error"
        with self.assertRaises(AssertionError) as exc:
            self.hotAssertAliasReferences(self.post, 'author_fk', halftest.Comment)
        self.assertEqual(str(exc.exception), "Post.author_fk() does not reference Comment")
