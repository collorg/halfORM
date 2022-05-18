#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from unittest import TestCase
import psycopg2

from ..init import halftest, model
from half_orm.pg_metaview import PgMeta

class Test(TestCase):
    def setUp(self):
        self.conn = psycopg2.connect(**{'dbname': 'halftest', 'password': 'halftest'})
        self.pg_meta = PgMeta(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_is_connected(self):
        self.assertEqual(self.conn.get_dsn_parameters()['dbname'], 'halftest')
