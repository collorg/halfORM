#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from unittest import TestCase

import psycopg2

from ..init import halftest

class Test(TestCase):
    def setUp(self):
        self.pers = halftest.Person()()
        self.post = halftest.Post()()
        self.relation = halftest.relation

    def test_isinstance(self):
        pers = self.pers()
        self.assertTrue(isinstance(pers, self.pers.__class__))

    def test_schemaname(self):
        "_schemaname should be 'actor' for the halftest.Person() class"
        self.assertEqual(halftest.Person()._schemaname, "actor")

    def test_tablename(self):
        "_relationname should be 'person' for the halftest.Person() class"
        self.assertEqual(halftest.Person()._relationname, "person")

    def test_add_returning(self):
        "it should return a returning clause"
        add_returning = self.pers.__class__.__bases__[0].__dict__['__add_returning'].__get__(object)
        self.assertEqual(add_returning('query', 'a', 'b'), 'query returning a, b')
        self.assertEqual(add_returning('query'), 'query')

    def test_ho_is_frozen(self):
        frozen = self.pers.__dict__['__isfrozen']
        self.assertEqual(True, frozen)
        self.pers._ho_unfreeze()
        frozen = self.pers.__dict__['__isfrozen']
        self.assertEqual(False, frozen)
        self.pers._ho_freeze()
        frozen = self.pers.__dict__['__isfrozen']
        self.assertEqual(True, frozen)

    def test_ho_unaccent(self):
        self.assertFalse(self.pers.first_name.unaccent)
        self.assertFalse(self.pers.last_name.unaccent)
        self.pers._ho_unaccent('first_name', 'last_name')
        self.assertTrue(self.pers.first_name.unaccent)
        self.assertTrue(self.pers.last_name.unaccent)

    def test_ho_unaccent_error(self):
        class Person(halftest.model.get_relation_class('actor.person')):
            def __init__(self):
                self.coucou = 'coucou'
        pers = Person()
        with self.assertRaises(ValueError) as exc:
            pers._ho_unaccent('coucou')
        self.assertEqual("coucou is not a Field!", str(exc.exception))
