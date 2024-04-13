#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from half_orm.hotest import HoTestCase

from ..init import halftest

class Test(HoTestCase):
    def setUp(self):
        self.pers = halftest.person_cls()
        self.post = halftest.post_cls()

    def test_references(self):
        "it should pass"
        self.hotAssertReferences(self.post, 'author', halftest.person_cls)
        self.hotAssertReferences(self.post, '_reverse_fkey_halftest_blog_comment_post_id', halftest.comment_cls)

    def test_references_error(self):
        "it should raise an error"
        with self.assertRaises(AssertionError) as exc:
            self.hotAssertReferences(self.post, 'author', halftest.comment_cls)
        self.assertEqual(str(exc.exception), "Post()._ho_fkeys['author']() does not reference Comment")

    def test_alias_references(self):
        "it should pass"
        self.hotAssertAliasReferences(self.post, 'author_fk', halftest.person_cls)
        self.hotAssertAliasReferences(self.post, 'comment_rfk', halftest.comment_cls)

    def test_alias_references_error(self):
        "it should raise an error"
        with self.assertRaises(AssertionError) as exc:
            self.hotAssertAliasReferences(self.post, 'author_fk', halftest.comment_cls)
        self.assertEqual(str(exc.exception), "Post.author_fk() does not reference Comment")
