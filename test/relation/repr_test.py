#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

import re
import sys
from time import sleep
from random import randint
from unittest import TestCase
import psycopg2
from half_orm.hotest import HoTestCase

from ..init import halftest
from half_orm import relation_errors, model

PERS_REPR = """DATABASE: halftest
SCHEMA: blog
TABLE: post

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

SET_PERS_REPR = """DATABASE: halftest
SCHEMA: actor
TABLE: person

DESCRIPTION:
The table actor.person contains the persons of the blogging system.
The id attribute is a serial. Just pass first_name, last_name and birth_date
to insert a new person.
FIELDS:
- id:         (int4) NOT NULL
- first_name: (text) NOT NULL (first_name = Gaston)
- last_name:  (text) NOT NULL (last_name = Lagaffe)
- birth_date: (date) NOT NULL (birth_date <= 1970-01-01)

PRIMARY KEY (first_name, last_name, birth_date)
UNIQUE CONSTRAINT (id)
UNIQUE CONSTRAINT (first_name)
FOREIGN KEYS:
- _reverse_fkey_halftest_blog_comment_author_id: ("id")
 ↳ "halftest":"blog"."comment"(author_id)
- _reverse_fkey_halftest_blog_event_author_first_name_author_last_name_author_birth_date: ("birth_date", "first_name", "last_name")
 ↳ "halftest":"blog"."event"(author_first_name, author_last_name, author_birth_date)
- _reverse_fkey_halftest_blog_post_author_first_name_author_last_name_author_birth_date: ("birth_date", "first_name", "last_name")
 ↳ "halftest":"blog"."post"(author_first_name, author_last_name, author_birth_date)

To use the foreign keys as direct attributes of the class, copy/paste the Fkeys below into
your code as a class attribute and replace the empty string key(s) with the alias(es) you
want to use. The aliases must be unique and different from any of the column names. Empty
string keys are ignored.

Fkeys = {
    '': '_reverse_fkey_halftest_blog_comment_author_id',
    '': '_reverse_fkey_halftest_blog_event_author_first_name_author_last_name_author_birth_date',
    '': '_reverse_fkey_halftest_blog_post_author_first_name_author_last_name_author_birth_date',
}"""

PERS_POSTS="""DATABASE: halftest
SCHEMA: blog
TABLE: post

DESCRIPTION:
The table blog.post contains all the post
made by a person in the blogging system.
FIELDS:
- id:                (int4) NOT NULL
- title:             (text)  (title = Easy)
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
- _reverse_...............: ("author_birth_date", "author_first_name", "author_last_name")
 ↳ "halftest":"blog"."post"("first_name", "last_name", "birth_date")
     DATABASE: halftest
     SCHEMA: actor
     TABLE: person
     
     DESCRIPTION:
     The table actor.person contains the persons of the blogging system.
     The id attribute is a serial. Just pass first_name, last_name and birth_date
     to insert a new person.
     FIELDS:
     - id:         (int4) NOT NULL
     - first_name: (text) NOT NULL (first_name = Gaston)
     - last_name:  (text) NOT NULL (last_name = Lagaffe)
     - birth_date: (date) NOT NULL (birth_date <= 1970-01-01)
     
     PRIMARY KEY (first_name, last_name, birth_date)
     UNIQUE CONSTRAINT (id)
     UNIQUE CONSTRAINT (first_name)
     FOREIGN KEYS:
     - _reverse_fkey_halftest_blog_comment_author_id: ("id")
      ↳ "halftest":"blog"."comment"(author_id)
     - _reverse_fkey_halftest_blog_event_author_first_name_author_last_name_author_birth_date: ("birth_date", "first_name", "last_name")
      ↳ "halftest":"blog"."event"(author_first_name, author_last_name, author_birth_date)
     - _reverse_fkey_halftest_blog_post_author_first_name_author_last_name_author_birth_date: ("birth_date", "first_name", "last_name")
      ↳ "halftest":"blog"."post"(author_first_name, author_last_name, author_birth_date)
     
     To use the foreign keys as direct attributes of the class, copy/paste the Fkeys below into
     your code as a class attribute and replace the empty string key(s) with the alias(es) you
     want to use. The aliases must be unique and different from any of the column names. Empty
     string keys are ignored.
     
     Fkeys = {
         '': '_reverse_fkey_halftest_blog_comment_author_id',
         '': '_reverse_fkey_halftest_blog_event_author_first_name_author_last_name_author_birth_date',
         '': '_reverse_fkey_halftest_blog_post_author_first_name_author_last_name_author_birth_date',
     }

To use the foreign keys as direct attributes of the class, copy/paste the Fkeys below into
your code as a class attribute and replace the empty string key(s) with the alias(es) you
want to use. The aliases must be unique and different from any of the column names. Empty
string keys are ignored.

Fkeys = {
    '': '_reverse_fkey_halftest_blog_comment_post_id',
    '': 'author',
    '': '_reverse_...............',
}"""

class Test(HoTestCase):
    def setUp(self):
        self.Post = halftest.post_cls
        self.pers = halftest.person_cls()
        self.pers.last_name = 'Lagaffe'
        self.pers.first_name = 'Gaston'
        self.pers.birth_date = ('<=', '1970-01-01')

    def test_rel(self):
        self.maxDiff = None
        self.assertEqual(''.join(repr(self.Post())), PERS_REPR)

    def test_set_rel(self):
        self.maxDiff = None
        self.assertEqual(''.join(repr(self.pers)), SET_PERS_REPR)

    def test_repr_with_fkey_set(self):
        self.maxDiff = None
        posts = self.pers.post_rfk(title='Easy')
        res = ''.join(repr(posts))
        res = re.sub(r'_reverse_\d{15}', '_reverse_...............', res, 2)
        self.assertEqual(res, PERS_POSTS)
