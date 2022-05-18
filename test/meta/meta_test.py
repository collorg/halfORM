#!/usr/bin/env python3
# -*- coding:  utf-8 -*-

import os
import psycopg2
from unittest import TestCase
from psycopg2.extras import RealDictCursor
from configparser import ConfigParser

from ..init import halftest, model
from half_orm.pg_meta import PgMeta


HALFTEST_DESC = [
    ('r', '"halftest":"actor"."person"', []),
    ('r', '"halftest":"blog"."comment"', []),
    ('r', '"halftest":"blog"."event"', ['"halftest":"blog"."post"']),
    ('r', '"halftest":"blog"."post"', []),
    ('v', '"halftest":"blog.view"."post_comment"', [])
]

CONF_DIR = os.path.abspath(os.environ.get('HALFORM_CONF_DIR', '/etc/half_orm'))

class Test(TestCase):
    def setUp(self):
        self.pg_meta = model._Model__pg_meta

    def tearDown(self):
        model.disconnect()

    def test_desc(self):
        "it should return the list of relations as [(<type>, <fqrn>, [<inherits>, ...]), ...]"
        self.assertEqual(self.pg_meta.desc('halftest'), HALFTEST_DESC)
