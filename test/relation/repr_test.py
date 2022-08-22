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

PERS_REPR = '__RCLS: <class \'halftest.actor.person.Person\'>\nThis class allows you to manipulate the data in the PG relation:\nTABLE: "halftest":"actor"."person"\nDESCRIPTION:\nThe table actor.person contains the persons of the blogging system.\nThe id attribute is a serial. Just pass first_name, last_name and birth_date\nto insert a new person.\nFIELDS:\n- id:         (int4) NOT NULL\n- first_name: (text) NOT NULL\n- last_name:  (text) NOT NULL\n- birth_date: (date) NOT NULL\n\nPRIMARY KEY (first_name, last_name, birth_date)\nUNIQUE CONSTRAINT (id)\nUNIQUE CONSTRAINT (first_name)\nFOREIGN KEYS:\n- _reverse_fkey_halftest_blog_comment_author_id: ("id")\n ↳ "halftest":"blog"."comment"(author_id)\n- _reverse_fkey_halftest_blog_event_author_first_name_author_last_name_author_birth_date: ("birth_date", "first_name", "last_name")\n ↳ "halftest":"blog"."event"(author_first_name, author_last_name, author_birth_date)\n- _reverse_fkey_halftest_blog_post_author_first_name_author_last_name_author_birth_date: ("birth_date", "first_name", "last_name")\n ↳ "halftest":"blog"."post"(author_first_name, author_last_name, author_birth_date)\n\nTo use the foreign keys as direct attributes of the class, copy/paste the Fkeys bellow in\nyour code as a class attribute and replace the empty string(s) key(s) with the alias you\nwant to use. The aliases must be unique and different from any of the column names. Empty\nstring keys are ignored.\n\nFkeys = {\n    \'\': \'_reverse_fkey_halftest_blog_comment_author_id\',\n    \'\': \'_reverse_fkey_halftest_blog_event_author_first_name_author_last_name_author_birth_date\',\n    \'\': \'_reverse_fkey_halftest_blog_post_author_first_name_author_last_name_author_birth_date\',\n}'


class Test(HoTestCase):
    def setUp(self):
        self.pers = halftest.pers

    def test_rel(self):
        self.maxDiff = None
        self.assertEqual(''.join(repr(self.pers)), PERS_REPR)
