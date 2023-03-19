#!/usr/bin/env python
#-*- coding:  utf-8 -*-

from random import randint
import psycopg2
import sys
from unittest import TestCase
from datetime import date

from ..init import halftest
from half_orm import relation_errors, model

class Test(TestCase):
    def setUp(self):
        self.gaston = halftest.gaston
        self.gaston._ho_insert()
        self.gaston.post_rfk(title='Easy', content='bla')._ho_insert()
        self.gaston.post_rfk(title='Super', content='bli')._ho_insert()
        self.gaston.post_rfk(title='Super easy', content='blu')._ho_insert()
        self.gaston.post_rfk(title='Bad', content='blo')._ho_insert()

    def tearDown(self):
        self.gaston._ho_delete()

    def test_or_on_fkeys(self):
        posts = self.gaston.post_rfk(title=('ilike', '%easy%')) | self.gaston.post_rfk(title=('ilike', '%super%'))
        list(posts)
        self.assertEqual(len(posts), 3)
        posts = self.gaston.post_rfk(title=('ilike', '%easy%')) & self.gaston.post_rfk(title=('ilike', '%super%'))
        list(posts)
        self.assertEqual(len(posts), 1)
