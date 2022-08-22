#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from time import sleep
from random import randint
import psycopg2
import sys
from unittest import TestCase
from half_orm.hotest import HoTestCase

from ..init import halftest
from half_orm import relation_errors, model

PERS_REPR = '__RCLS: <class \'halftest.blog.post.Post\'>\nThis class allows you to manipulate the data in the PG relation:\nTABLE: "halftest":"blog"."post"\nDESCRIPTION:\nThe table blog.post contains all the post\nmade by a person in the blogging system.\nFIELDS:\n- id:                (int4) NOT NULL\n- title:             (text)\n- content:           (text)\n- author_first_name: (text)\n- author_last_name:  (text)\n- author_birth_date: (date)\n\nPRIMARY KEY (id)\nUNIQUE CONSTRAINT (title, content)\nFOREIGN KEYS:\n- _reverse_fkey_halftest_blog_comment_post_id: ("id")\n ↳ "halftest":"blog"."comment"(post_id)\n- author: ("author_birth_date", "author_first_name", "author_last_name")\n ↳ "halftest":"actor"."person"(first_name, last_name, birth_date)\n\nTo use the foreign keys as direct attributes of the class, copy/paste the Fkeys bellow in\nyour code as a class attribute and replace the empty string(s) key(s) with the alias you\nwant to use. The aliases must be unique and different from any of the column names. Empty\nstring keys are ignored.\n\nFkeys = {\n    \'\': \'_reverse_fkey_halftest_blog_comment_post_id\',\n    \'\': \'author\',\n}'


class Test(HoTestCase):
    def setUp(self):
        self.Post = halftest.Post

    def test_rel(self):
        self.maxDiff = None
        self.assertEqual(''.join(repr(self.Post())), PERS_REPR)
