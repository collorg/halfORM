#!/usr/bin/env python
#-*- coding:  utf-8 -*-

import contextlib
import io
import sys
import psycopg2
from random import randint
from unittest import TestCase
from datetime import date

from ..init import halftest, GASTON, model
from half_orm import relation_errors
from half_orm.relation import Relation

class Test(TestCase):
    maxDiff = None
    def setUp(self):
        self.gaston = halftest.gaston
        self.gaston.ho_insert()
        self.post = halftest.post_cls()
        self.gaston.event_rfk(title='Easy', content='bla').ho_insert()
        self.gaston.post_rfk(title='Super', content='bli').ho_insert()
        self.gaston.post_rfk(title='A super easy', content='blo').ho_insert()
        self.gaston.post_rfk(title='Bad', content='blu').ho_insert()
        model.execute_query('create table column_alias_test(class int, "class + 1" int, "2 + 1" int)')
        model.reconnect(reload=True)
        self.ColumnAliasTest = model.get_relation_class(
            'public.column_alias_test',
            fields_aliases={'class': 'class_', 'class + 1': 'class_plus_one'})

    def tearDown(self):
        self.gaston.ho_delete()
        model.execute_query('drop table column_alias_test')
        model.reconnect(reload=True)

    def testho_only(self):
        posts1 = self.gaston.post_rfk(title=('ilike', '%easy%'))
        posts1.ho_only = False
        self.assertEqual(posts1.ho_count(), 2)
        posts2 = self.gaston.post_rfk(title=('ilike', '%super%'))
        posts = posts1 | posts2
        list(posts)
        self.assertEqual(posts.ho_count(), 3)
        posts1.ho_only = True
        self.assertEqual(posts1.ho_count(), 1)
        posts = self.gaston.post_rfk(title=('ilike', '%easy%')) & self.gaston.post_rfk(title=('ilike', '%super%'))
        list(posts)
        self.assertEqual(posts.ho_count(), 1)

    def testho_only_accepts_only_bool_values(self):
        "ho_only should only accept boolean values"
        with self.assertRaises(ValueError) as err:
            self.post.ho_only = 'coucou'
        self.assertEqual(str(err.exception), 'coucou is not a bool!')

    def testho_dict(self):
        "it should return the dict with the set values"
        self.assertEqual(self.gaston.ho_dict(), GASTON)

    def testho_dict_empty(self):
        "it should return an empty dict if the relation is not constrain"
        self.assertEqual(halftest.person_cls().ho_dict(), {})

    def testho_order_by(self):
        "it should return the set ordered by..."
        list_ = ['Easy', 'Super', 'A super easy', 'Bad']
        posts = halftest.post_cls().ho_order_by('content, title')
        self.assertEqual([elt['title'] for elt in list(posts)], list_)
        posts = halftest.post_cls().ho_order_by('title')
        ordered_list_on_title = list(list_)
        ordered_list_on_title.sort()
        self.assertEqual([elt['title'] for elt in list(posts)], ordered_list_on_title)
        posts = halftest.post_cls().ho_order_by('title desc')
        ordered_list_on_title_reversed = list(ordered_list_on_title)
        ordered_list_on_title_reversed.reverse()
        self.assertEqual([elt['title'] for elt in list(posts)], ordered_list_on_title_reversed)

    def testho_limit(self):
        "it should return the set limited to limit"
        limit = randint(1, halftest.post_cls().ho_count())
        posts = halftest.post_cls().ho_order_by('content, title').ho_limit(limit)
        self.assertEqual(len(list(posts)), limit)

    def testho_limit_with_no_limit(self):
        "it should return the set"
        posts = halftest.post_cls()
        posts.ho_limit(1)
        self.assertEqual(len(list(posts)), 1)
        posts.ho_limit(0)
        self.assertEqual(len(list(posts)), halftest.post_cls().ho_count())

    def test_ho_limit_error(self):
        "it should raise an error"
        posts = halftest.post_cls()
        with self.assertRaises(ValueError):
            posts.ho_limit("a")

    def test_ho_offset(self):
        "it should set the offset"
        posts = halftest.post_cls()
        offset = randint(0, halftest.post_cls().ho_count())
        posts.ho_offset(offset)
        self.assertEqual(len(list(posts)), halftest.post_cls().ho_count() - offset)

    def test_ho_offset_error(self):
        "it should raise an error"
        posts = halftest.post_cls()
        with self.assertRaises(ValueError):
            posts.ho_offset("a")

    def test_cast(self):
        "it should cast to the new relation"
        events = halftest.post_cls().ho_cast('blog.event')
        self.assertEqual(events.ho_count(), 1)

    def test_cast_error(self):
        "it should raise an error if the set attributes are not known in the new relation"
        with self.assertRaises(relation_errors.UnknownAttributeError) as exc:
            halftest.post_cls(title='coucou').ho_cast('actor.person')
        self.assertEqual(str(exc.exception), "ERROR! Unknown attribute: title.")

    def test_field_aliases(self):
        self.assertEqual('class_', self.ColumnAliasTest._Relation__py_field_name('class', 1))
        self.assertEqual('class_plus_one', self.ColumnAliasTest._Relation__py_field_name('class + 1', 2))
        self.assertEqual('column3', self.ColumnAliasTest._Relation__py_field_name('1 + 1', 3))
        self.ColumnAliasTest().class_.set(3)
        self.ColumnAliasTest(class_plus_one=4, column3=12)
        self.assertEqual(self.ColumnAliasTest().column3.name, '2 + 1')
        
    def test_wrong_fiel_name_err_msg(self):
        out = io.StringIO()
        value1 = ''
        with contextlib.redirect_stderr(out):
            self.ColumnAliasTest()
            value1 = out.getvalue()
        self.assertEqual(value1, '\x1b[1mHOP WARNING\x1b[0m: "\x1b[1m2 + 1\x1b[0m" is not a valid identifier in Python.\n')
