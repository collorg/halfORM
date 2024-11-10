#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

import uuid
from unittest import TestCase
from half_orm.relation import Relation
from half_orm.relation_errors import IsFrozenError

import psycopg2

from ..init import halftest

PERS_REPR = """DATABASE: halftest
SCHEMA: actor
TABLE: person

DESCRIPTION:
The table actor.person contains the persons of the blogging system. The id attribute is a serial. Just pass first_name, last_name and birth_date to insert a new person.
FIELDS:
- id:         (int4) NOT NULL
- first_name: (text) NOT NULL
- last_name:  (text) NOT NULL
- birth_date: (date) NOT NULL

PRIMARY KEY (first_name, last_name, birth_date)
UNIQUE CONSTRAINT (id)
UNIQUE CONSTRAINT (last_name)
FOREIGN KEYS:
- _reverse_fkey_halftest_blog_comment_author_id: ("id")
 ↳ "halftest":"blog"."comment"(author_id)
- _reverse_fkey_halftest_blog_event_author_first_name_author_last_name_author_birth_date: ("first_name", "last_name", "birth_date")
 ↳ "halftest":"blog"."event"(author_first_name, author_last_name, author_birth_date)
- _reverse_fkey_halftest_blog_post_author_first_name_author_last_name_author_birth_date: ("first_name", "last_name", "birth_date")
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

FROZEN_ERROR = """ERROR! The class <class 'halftest.actor.person.Person'> is forzen.
Use ho_unfreeze to add the 'coucou' attribute to it."""

class Test(TestCase):
    def setUp(self):
        self.pers = halftest.person_cls()()
        self.post = halftest.post_cls()()
        self.relation = halftest.relation

    def test_relation_is_callable(self):
        self.assertIsInstance(self.pers, Relation)

    def test_isinstance(self):
        pers = self.pers()
        self.assertTrue(isinstance(pers, self.pers.__class__))

    def test_schemaname(self):
        "_schemaname should be 'actor' for the halftest.person_cls() class"
        self.assertEqual(halftest.person_cls()._schemaname, "actor")

    def test_tablename(self):
        "_relationname should be 'person' for the halftest.person_cls() class"
        self.assertEqual(halftest.person_cls()._relationname, "person")

    def test_add_returning(self):
        "it should return a returning clause"
        add_returning = self.pers.__class__._ho_add_returning
        self.assertEqual(add_returning(self.pers, 'query', 'a', 'b'), 'query returning a, b')
        self.assertEqual(add_returning(self.pers, 'query'), 'query')

    def testho_is_frozen(self):
        pers = self.pers()
        self.assertTrue(pers._ho_isfrozen)
        with self.assertRaises(IsFrozenError) as exc:
            setattr(pers, 'coucou', None)
        self.assertEqual(FROZEN_ERROR, str(exc.exception))
        pers.ho_unfreeze()
        self.assertFalse(pers._ho_isfrozen)
        setattr(pers, 'coucou', 1)
        pers.ho_freeze()
        self.assertTrue(pers._ho_isfrozen)

    def testho_unaccent(self):
        self.assertFalse(self.pers.first_name.unaccent)
        self.assertFalse(self.pers.last_name.unaccent)
        self.pers.ho_unaccent('first_name', 'last_name')
        self.assertTrue(self.pers.first_name.unaccent)
        self.assertTrue(self.pers.last_name.unaccent)

    def testho_unaccent_error(self):
        class Person(halftest.model.get_relation_class('actor.person')):
            def __init__(self):
                self.coucou = 'coucou'
        pers = Person()
        with self.assertRaises(ValueError) as exc:
            pers.ho_unaccent('coucou')
        self.assertEqual("coucou is not a Field!", str(exc.exception))

    def test_repr(self):
        self.maxDiff = None
        person_cls = halftest.model.get_relation_class('actor.person')
        self.assertEqual(person_cls().__repr__(), PERS_REPR)

    def test_ho_is_empty(self):
        empty = self.pers()
        empty.first_name.set(str(uuid.uuid4()))
        self.assertTrue(empty.ho_is_empty())
        not_empty = self.pers()
        self.assertFalse(not_empty.ho_is_empty())

    def test_ho_count_limit(self):
        pers = self.pers()
        pers.ho_limit(2)
        self.assertEqual(pers.ho_count(), 2)

    def test_ho_count_distinct(self):
        pers = self.pers()
        pers.ho_mogrify()
        pers.ho_distinct()
        self.assertEqual(pers.ho_count('birth_date'), 1)
        pers.ho_distinct(False)
        self.assertEqual(pers.ho_count('birth_date'), 60)

    def test_ho_count_arg(self):
        with self.assertRaises(ValueError) as exc:
            self.pers().ho_distinct(2)
        self.assertEqual("ho_distinct argument must be either True or False!", str(exc.exception))

    def test_keys(self):
        self.assertEqual(list(self.pers.keys()), ['id', 'first_name', 'last_name', 'birth_date'])

    def test_items(self):
        pers = self.pers(first_name='Gaston', last_name='Lagaffe')
        self.assertEqual(list(pers.items()), [('id', None), ('first_name', 'Gaston'), ('last_name', 'Lagaffe'), ('birth_date', None)])

    def test_getitem(self):
        pers = self.pers(first_name='Gaston', last_name='Lagaffe')
        self.assertEqual(pers['last_name'], 'Lagaffe')
