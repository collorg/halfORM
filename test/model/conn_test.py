#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from unittest import TestCase
from psycopg2 import InterfaceError

from ..init import halftest, model

class Test(TestCase):
    def reset(self):
        pass

    def test_connection(self):
        self.assertEqual(halftest.dbname, 'halftest')

    def test_relation_instanciation(self):
        person = halftest.relation("actor.person")
        self.assertEqual(person._fqrn, '"halftest":"actor"."person"')
        post = halftest.relation("blog.post")
        self.assertEqual(post._fqrn, '"halftest":"blog"."post"')
        person = halftest.relation("blog.comment")
        self.assertEqual(person._fqrn, '"halftest":"blog"."comment"')
        person = halftest.relation("blog.view.post_comment")
        self.assertEqual(person._fqrn, '"halftest":"blog.view"."post_comment"')

    def test_disconnect(self):
        "it should disconnect"
        model.disconnect()
        with self.assertRaises(InterfaceError):
            model.execute_query("select 1")

    def test_ping(self):
        "it shoud reconnect"
        model.disconnect()
        model.ping()
        self.assertEqual(1, model.execute_query("select 1").fetchone()['?column?'])