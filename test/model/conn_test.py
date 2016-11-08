#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

import os.path
from unittest import TestCase
from ..init import halftest
from half_orm.model import Model

class Test(TestCase):
    def reset(self):
        pass

    def connection_test(self):
        self.assertEqual(halftest.dbname, 'halftest')

    def relation_instanciation_test(self):
        person = halftest.relation("actor.person")
        self.assertEqual(person._fqrn, '"halftest"."actor"."person"')
        post = halftest.relation("blog.post")
        self.assertEqual(post._fqrn, '"halftest"."blog"."post"')
        person = halftest.relation("blog.comment")
        self.assertEqual(person._fqrn, '"halftest"."blog"."comment"')
        person = halftest.relation("blog.view.post_comment")
        self.assertEqual(person._fqrn, '"halftest"."blog.view"."post_comment"')
