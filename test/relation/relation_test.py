#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from unittest import TestCase

import psycopg2

from ..init import halftest

class Test(TestCase):
    def setUp(self):
        self.pers = halftest.person_cls()()
        self.post = halftest.post_cls()()
        self.relation = halftest.relation

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
        add_returning = self.pers.__class__.__bases__[0].__dict__['__add_returning'].__get__(object)
        self.assertEqual(add_returning('query', 'a', 'b'), 'query returning a, b')
        self.assertEqual(add_returning('query'), 'query')

    def testho_is_frozen(self):
        frozen = self.pers.__dict__['__isfrozen']
        self.assertTrue(frozen)
        self.pers.ho_unfreeze()
        frozen = self.pers.__dict__['__isfrozen']
        self.assertFalse(frozen)
        self.pers.ho_freeze()
        frozen = self.pers.__dict__['__isfrozen']
        self.assertTrue(frozen)

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
