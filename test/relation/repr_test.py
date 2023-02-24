#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

import sys
from time import sleep
from random import randint
from unittest import TestCase
import psycopg2
from half_orm.hotest import HoTestCase

from ..init import halftest
from half_orm import relation_errors, model

PERS_REPR = """__RCLS: <class 'halftest.blog.post.Post'>
This class allows you to manipulate the data in the PG relation:
TABLE: "halftest":"blog"."post"
DESCRIPTION:
The table blog.post contains all the post
made by a person in the blogging system.
FIELDS:
- id:                (int4) NOT NULL
- title:             (text)
- content:           (text)
- author_first_name: (text)
- author_last_name:  (text)
- author_birth_date: (date)
- data:              (jsonb)

PRIMARY KEY (id)
UNIQUE CONSTRAINT (title, content)
FOREIGN KEYS:
- _reverse_fkey_halftest_blog_comment_post_id: ("id")
 ↳ "halftest":"blog"."comment"(post_id)
- author: ("author_birth_date", "author_first_name", "author_last_name")
 ↳ "halftest":"actor"."person"(first_name, last_name, birth_date)

To use the foreign keys as direct attributes of the class, copy/paste the Fkeys below into
your code as a class attribute and replace the empty string key(s) with the alias(es) you
want to use. The aliases must be unique and different from any of the column names. Empty
string keys are ignored.

Fkeys = {
    '': '_reverse_fkey_halftest_blog_comment_post_id',
    '': 'author',
}"""

class Test(HoTestCase):
    def setUp(self):
        self.Post = halftest.Post

    def test_rel(self):
        self.maxDiff = None
        self.assertEqual(''.join(repr(self.Post())), PERS_REPR)
