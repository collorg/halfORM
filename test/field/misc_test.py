#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from unittest import TestCase
from datetime import date

from half_orm.field import Field
from half_orm.null import NULL

from ..init import halftest

class Test(TestCase):
    def setUp(self):
        self.pers = halftest.person_cls()
        self.post = halftest.post_cls()
        self.today = halftest.today

    def tearDown(self):
        halftest.model.execute_query('alter table blog.post alter column content drop not null')
        halftest.model.reconnect(reload=True)
        self.pers(last_name=('like', '____')).ho_delete()

    def test_not_set_field(self):
        fields_set = {elt.is_set() for elt in self.pers._ho_fields.values()}
        self.assertTrue(fields_set, {False})

    def test_set_field(self):
        pers = self.pers(first_name='jojo')
        self.assertTrue(pers.first_name.is_set())

    def test_idem(self):
        pers = self.pers(first_name='jojo')
        self.assertIsInstance(pers.first_name, Field)

    def test_fields_names(self):
        field_names = set(self.pers._ho_fields.keys())
        self.assertEqual(
            field_names,
            {'id', 'first_name', 'last_name', 'birth_date'})

    def test_relation_ref(self):
        first_name = self.pers.first_name
        self.assertEqual(id(first_name._relation), id(self.pers))

    def test_unset_field_with_none(self):
        pers = self.pers(first_name='jojo')
        pers.first_name.set(None)
        self.assertEqual(len(pers), len(self.pers))
        self.assertFalse(pers.first_name.is_set())

    def test_is_not_null(self):
        post = halftest.post_cls()
        self.assertFalse(post.content.is_not_null())
        halftest.model.execute_query('alter table blog.post alter column content set not null')
        halftest.model.reconnect(reload=True)
        post = halftest.post_cls()
        self.assertTrue(post.content.is_not_null())
        halftest.model.execute_query('alter table blog.post alter column content drop not null')
        halftest.model.reconnect(reload=True)

    def test_relation(self):
        post = halftest.post_cls()
        self.assertEqual(post.content._relation, halftest.post_cls())

    def test_str_value(self):
        self.post.content = 10
        self.assertEqual(str(10), str(self.post.content))
        self.post.content = ('ilike', '%10%')
        self.assertEqual('%10%', str(self.post.content))
        self.post.content = date.today()
        self.assertEqual(str(date.today()), str(self.post.content))

    def test_wrong_value(self):
        with self.assertRaises(ValueError) as exc:
            self.post.content = ('=', 'b', 'c')
        self.assertEqual("Can't match ('=', 'b', 'c') with (comp, value)!", str(exc.exception))

    def test_null_value(self):
        self.post.content = NULL
        self.assertEqual(self.post.content._comp(), 'is')
        list(self.post)

    def test_comp_is_none_error(self):
        with self.assertRaises(ValueError) as exc:
            self.post.content = ('=', None)
        self.assertEqual("Can't have a None value with a comparator!", str(exc.exception))

    def test_comp_should_be_is_error(self):
        with self.assertRaises(ValueError) as exc:
            self.post.content = ('!=', NULL)
        self.assertEqual("comp should be 'is' or 'is not' with NULL value!", str(exc.exception))

    def test_comp_pct(self):
        self.post.content = ('%', 'what ever')
        self.assertEqual('%%', str(self.post.content._comp()))

    def test_unaccent(self):
        self.assertFalse(self.post.content.unaccent)
        self.post.content.unaccent = True
        self.assertTrue(self.post.content.unaccent)

        with self.assertRaises(RuntimeError) as exc:
            self.post.content.unaccent = 'true'
        self.assertEqual("unaccent value must be True or False!", str(exc.exception))

    def test_name_property(self):
        self.assertEqual(self.post.content._name, self.post.content._Field__name)
        self.assertEqual(self.post.content._name, 'content')
        self.assertEqual(self.pers.last_name._name, 'last_name')

    def test_repr(self):
        self.assertEqual(repr(self.post.content), '(text)')
        self.assertEqual(repr(self.post.id), '(int4) NOT NULL')
        self.assertEqual(repr(self.pers.birth_date), '(date) NOT NULL')

        self.pers.birth_date = date.today()
        self.assertEqual(repr(self.pers.birth_date), f'(date) NOT NULL (birth_date = {date.today()})')

    def test_comps(self):
        self.post.content = ('@@', 'bonjour')
        self.assertEqual(self.post.content._where_repr('', id(self.post)), '"content" @@ websearch_to_tsquery(%s)')
        self.post.content = ('=', ('bonjour', 'au revoir'))
        self.assertEqual(self.post.content._where_repr('', id(self.post)), '"content" = any(%s)')
        self.post.content = ('@@', ('bonjour', 'au revoir'))
        self.assertEqual(self.post.content._where_repr('', id(self.post)), '"content" @@ any(websearch_to_tsquery(%s))')
        self.post.content.unaccent = True
        self.assertEqual(self.post.content._where_repr('', id(self.post)), 'unaccent("content") @@ unaccent(any(websearch_to_tsquery(%s)))')

    def test_set_with_field(self):
        abcd_f1 = self.pers(first_name='abcd', last_name='abcd', birth_date=date(2019, 3, 4))
        abcd_f1.ho_insert()
        abcd_f2 = self.pers(first_name='abce', last_name='bcda', birth_date=date(2019, 3, 4))
        abcd_f2.ho_insert()
        bcda_f1 = self.pers(first_name='bcda', last_name='bcda', birth_date=date(2019, 3, 4))
        bcda_f1.ho_insert()
        bcda_f2 = self.pers(first_name='bcde', last_name='acda', birth_date=date(2019, 3, 4))
        bcda_f2.ho_insert()
        p1_set = self.pers(first_name=('like', '____'))
        p2_set = self.pers()
        p2_set.first_name.set(p2_set.last_name)
        p3_set = self.pers()
        p3_set.first_name.set(('!=', p3_set.last_name))
        p4_set = self.pers()
        p4_set.first_name.set(('>=', p4_set.last_name))
        p5_set = self.pers()
        p5_set.first_name.set(('<', p5_set.last_name))
        self.assertEqual(len(p2_set & p1_set), 2)
        self.assertEqual(len(p3_set & p1_set), 2)
        self.assertEqual(len(p2_set & p3_set), 0)
        self.assertEqual(len(p4_set & p1_set), 3)
        self.assertEqual(len(p5_set & p1_set), 1)
