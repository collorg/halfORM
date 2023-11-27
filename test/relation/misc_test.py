#!/usr/bin/env python
#-*- coding:  utf-8 -*-

from random import randint
import psycopg2
import sys
from unittest import TestCase
from datetime import date

from ..init import halftest, GASTON
from half_orm import relation_errors, model

class Test(TestCase):
    def setUp(self):
        self.gaston = halftest.gaston
        self.gaston.ho_insert()
        self.post = halftest.Post()
        self.gaston.event_rfk(title='Easy', content='bla').ho_insert()
        self.gaston.post_rfk(title='Super', content='bli').ho_insert()
        self.gaston.post_rfk(title='A super easy', content='blo').ho_insert()
        self.gaston.post_rfk(title='Bad', content='blu').ho_insert()

    def tearDown(self):
        self.gaston.ho_delete()
        pass

    def testho_only(self):
        posts1 = self.gaston.post_rfk(title=('ilike', '%easy%'))
        posts1.ho_only = False
        self.assertEqual(len(posts1), 2)
        posts2 = self.gaston.post_rfk(title=('ilike', '%super%'))
        posts = posts1 | posts2
        list(posts)
        self.assertEqual(len(posts), 3)
        posts1.ho_only = True
        self.assertEqual(len(posts1), 1)
        posts = self.gaston.post_rfk(title=('ilike', '%easy%')) & self.gaston.post_rfk(title=('ilike', '%super%'))
        list(posts)
        self.assertEqual(len(posts), 1)

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
        self.assertEqual(halftest.Person().ho_dict(), {})

    def testho_order_by(self):
        "it should return the set ordered by..."
        list_ = ['Easy', 'Super', 'A super easy', 'Bad']
        posts = halftest.Post().ho_order_by('content, title')
        self.assertEqual([elt['title'] for elt in list(posts)], list_)
        posts = halftest.Post().ho_order_by('title')
        ordered_list_on_title = list(list_)
        ordered_list_on_title.sort()
        self.assertEqual([elt['title'] for elt in list(posts)], ordered_list_on_title)
        posts = halftest.Post().ho_order_by('title desc')
        ordered_list_on_title_reversed = list(ordered_list_on_title)
        ordered_list_on_title_reversed.reverse()
        self.assertEqual([elt['title'] for elt in list(posts)], ordered_list_on_title_reversed)

    def testho_limit(self):
        "it should return the set limited to limit"
        limit = randint(1, len(halftest.Post()))
        posts = halftest.Post().ho_order_by('content, title').ho_limit(limit)
        self.assertEqual(len(list(posts)), limit)

    def testho_limit_with_no_limit(self):
        "it should return the set"
        posts = halftest.Post()
        posts.ho_limit(1)
        self.assertEqual(len(list(posts)), 1)
        posts.ho_limit(0)
        self.assertEqual(len(list(posts)), len(halftest.Post()))

    def testho_offset(self):
        "it should set the offset"
        posts = halftest.Post()
        offset = randint(0, len(halftest.Post()))
        posts.ho_offset(offset)
        self.assertEqual(len(list(posts)), len(halftest.Post()) - offset)

    def test_cast(self):
        "it should cast to the new relation"
        events = halftest.Post().ho_cast('blog.event')
        self.assertEqual(len(events), 1)

    def test_cast_error(self):
        "it should raise an error if the set attributes are not known in the new relation"
        with self.assertRaises(relation_errors.UnknownAttributeError) as exc:
            halftest.Post(title='coucou').ho_cast('actor.person')
        self.assertEqual(str(exc.exception), "ERROR! Unknown attribute: title.")
