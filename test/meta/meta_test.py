#!/usr/bin/env python3
# -*- coding:  utf-8 -*-

from unittest import TestCase

from ..init import halftest, model


HALFTEST_DESC = [
    ('r', ('halftest', 'actor', 'person'), []),
    ('r', ('halftest', 'blog', 'comment'), []),
    ('r', ('halftest', 'blog', 'event'), [('halftest', 'blog', 'post')]),
    ('r', ('halftest', 'blog', 'post'), []),
    ('v', ('halftest', 'blog.view', 'post_comment'), [])
]

HALFTEST_STR = """r "actor"."person"
r "blog"."comment"
r "blog"."event"
r "blog"."post"
v "blog.view"."post_comment"
"""

class Test(TestCase):
    def setUp(self):
        self.pg_meta = model._Model__pg_meta

    def tearDown(self):
        model.disconnect()

    def test_desc(self):
        "it should return the list of relations as [(<type>, <fqrn>, [<inherits>, ...]), ...]"
        self.assertEqual(self.pg_meta.desc('halftest'), HALFTEST_DESC)

    def test_str(self):
        "it should return a well formatted string"
        self.assertEqual(self.pg_meta.str('halftest'), HALFTEST_STR.strip())
