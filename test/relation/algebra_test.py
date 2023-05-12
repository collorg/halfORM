#!/usr/bin/env python
#-*- coding:  utf-8 -*-

from random import randint
import psycopg2
import sys
from unittest import TestCase
from datetime import date

from ..init import halftest
from half_orm import relation_errors, model
from half_orm.null import NULL

def name(letter, integer):
    return f"{letter}{chr(ord('a') + integer)}"

class Test(TestCase):
    def setUp(self):
        self.pers = halftest.Person()
        self.post = halftest.Post()
        self.today = halftest.today

        hexchars = 'abcdef'
        self.universe = self.pers()
        self.empty_set = self.pers(last_name=NULL)
        self.c1 = hexchars[randint(0, len(hexchars) - 1)]
        self.c2 = hexchars[randint(0, len(hexchars) - 1)]
        self.c3 = hexchars[randint(0, len(hexchars) - 1)]
        self.set_1 = self.pers(last_name=('like', f'{self.c1}%'))
        self.comp_set_1 = self.pers(
            last_name=('not like', f'{self.c1}%'))
        self.set_2 = self.pers(last_name=('like', f'_{self.c2}%'))
        self.subset_1_2 = self.pers(
            last_name=('like', f'{self.c1}{self.c2}%'))
        self.set_3 = self.pers(last_name=('like', f'__{self.c3}%'))

    def test_universe(self):
        self.assertGreaterEqual(len(self.universe), 60)

    def test_iand(self):
        a = self.set_1
        b = self.set_2
        c = a & b
        a &= b
        self.assertTrue(a, c)

    def test_ior(self):
        a = self.set_1
        b = self.set_2
        c = a | b
        a |= b
        self.assertTrue(a, c)

    def test_isub(self):
        a = self.set_1
        b = self.set_2
        c = a - b
        a -= b
        self.assertTrue(a, c)

    def test_xor(self):
        a = self.set_1
        b = self.set_2
        self.assertEqual(a ^ b, (a | b) - (a & b))

    def test_ixor(self):
        a = self.set_1
        b = self.set_2
        c = a ^ b
        a ^= b
        self.assertTrue(a, c)

    def test_and_1(self):
        a = self.set_1
        b = self.set_2
        self.assertTrue(a & b == a - ( a - b))

    def test_and_2(self):
        a = self.set_1
        b = self.set_2
        self.assertTrue(a & b == ((a | b) - (a - b) - ( b - a)))

    def test_and_3(self):
        a = self.set_1
        self.assertTrue(a & a == a)

    def test_and_4(self):
        a = self.set_1
        ab = self.subset_1_2
        self.assertTrue(a & ab == ab)

    def test_and_5(self):
        b = self.set_2
        ab = self.subset_1_2
        self.assertTrue(b & ab == ab)

    def test_and_6(self):
        a = self.set_1
        b = self.set_2
        ab = self.subset_1_2
        self.assertTrue(a & b == ab)

    def test_and_absorbing_elt(self):
        a = self.set_1
        empty = self.empty_set
        self.assertTrue(a & empty == empty)
        self.assertTrue(empty.ho_is_empty())

    def test_and_neutral_elt(self):
        a = self.set_1
        universe = self.universe
        self.assertTrue(universe & a == a)

    def test_or_1(self):
        a = self.set_1
        ab = self.subset_1_2
        self.assertTrue(a | ab == a)

    def test_or_2(self):
        b = self.set_2
        ab = self.subset_1_2
        self.assertTrue(b | ab == b)

    def test_or_neutral_elt(self):
        a = self.set_1
        empty = self.empty_set
        self.assertTrue(a | empty == a)

    def test_or_absorbing_elt_1(self):
        a = self.set_1
        universe = self.universe
        self.assertTrue(universe | a == universe)

    def test_or_absorbing_elt_2(self):
        a = self.set_1
        universe = self.universe
        self.assertTrue(a | universe == universe)

    def test_or_absorbing_elt_3(self):
        empty = self.empty_set
        self.assertTrue(empty | empty == empty)

    def test_not(self):
        a = self.set_1
        empty = self.empty_set
        self.assertTrue(a - empty == a)

    def test_empty(self):
        a = self.set_1
        empty = self.empty_set
        self.assertTrue(a - a == empty)

    def test_complementary_0(self):
        a = self.set_1
        comp_a = self.comp_set_1
        self.assertTrue(-a == comp_a)

    def test_complementary_1(self):
        a = self.set_1
        comp_a = self.comp_set_1
        universe = self.universe
        self.assertTrue(a | comp_a == universe)

    def test_complementary_2(self):
        a = self.set_1
        comp_a = self.comp_set_1
        self.assertTrue(a - comp_a == a)

    def test_symetric_difference(self):
        a = self.set_1
        b = self.set_2
        self.assertTrue((a - b) | (b - a) == (a | b) - (a & b))

    def test_commutative_laws_1(self):
        a = self.set_1
        b = self.set_2
        self.assertTrue(a & b == b & a)

    def test_commutative_laws_2(self):
        a = self.set_1
        b = self.set_2
        self.assertTrue(a | b == b | a)

    def test_associative_laws_1(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        self.assertTrue(a | (b | c) == (a | b) | c)

    def test_associative_laws_2(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        self.assertTrue(a & (b & c) == (a & b) & c)

    def test_distributive_laws_1(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        self.assertTrue(a | (b & c) == (a | b) & (a | c))

    def test_distributive_laws_2(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        self.assertTrue(a & (b | c) == (a & b) | (a & c))

    def test_identity_laws_1(self):
        a = self.set_1
        empty = self.empty_set
        self.assertTrue(a | empty == a)

    def test_identity_laws_2(self):
        a = self.set_1
        universe = self.universe
        self.assertTrue(a & universe == a)

    def test_complement_laws_1(self):
        a = self.set_1
        comp_a = self.comp_set_1
        universe = self.universe
        self.assertTrue(a | comp_a == universe)

    def test_complement_laws_2(self):
        a = self.set_1
        comp_a = self.comp_set_1
        empty = self.empty_set
        self.assertTrue(a & comp_a == empty)

    def test_complement_laws_3(self):
        a = self.set_1
        universe = self.universe
        self.assertTrue(a | (-a) == universe)

    def test_complement_laws_4(self):
        a = self.set_1
        empty = self.empty_set
        self.assertTrue(a & (-a) == empty)

    def test_idempotent_laws_1(self):
        a = self.set_1
        self.assertTrue(a | a == a)

    def test_idempotent_laws_2(self):
        a = self.set_1
        self.assertTrue(a & a == a)

    def test_domination_laws_1(self):
        a = self.set_1
        universe = self.universe
        self.assertTrue(a | universe == universe)

    def test_domination_laws_2(self):
        a = self.set_1
        empty = self.empty_set
        self.assertTrue(a & empty == empty)

    def test_absorption_laws_1(self):
        a = self.set_1
        b = self.set_2
        self.assertTrue(a | (a & b) == a)

    def test_absorption_laws_2(self):
        a = self.set_1
        b = self.set_2
        self.assertTrue(a & (a | b) == a)

    def test_de_morgan_s_laws_1(self):
        a = self.set_1
        b = self.set_2
        self.assertTrue((-a) | (-b) == -(a & b))

    def test_de_morgan_s_laws_2(self):
        a = self.set_1
        b = self.set_2
        self.assertTrue(-(a | b) == (-a) & (-b))

    def test_double_complement_law(self):
        a = self.set_1
        self.assertTrue(-(-a) == a)

    def test_empty_universe_complement(self):
        universe = self.universe
        empty = self.empty_set
        self.assertTrue(-empty == universe)

    def test_inclusion_1_0(self):
        a = self.set_1
        self.assertTrue(a in a)

    def test_inclusion_1_1(self):
        a = self.set_1
        ab = self.subset_1_2
        self.assertTrue(ab in a)

    def test_inclusion_1_2(self):
        b = self.set_2
        ab = self.subset_1_2
        self.assertTrue(ab in b)

    def test_ab_equal_a_inter_b(self):
        a = self.set_1
        b = self.set_2
        ab = self.subset_1_2
        self.assertTrue(ab == a & b)

    def test_inclusion_2(self):
        a = self.set_1
        empty = self.empty_set
        self.assertTrue(empty in a)

    def test_inclusion_3(self):
        a = self.set_1
        universe = self.universe
        self.assertTrue(a in universe)

    def test_inclusion_4_1(self):
        a = self.set_1
        b = self.set_2
        self.assertTrue(a in a | b)

    def test_inclusion_4_2(self):
        a = self.set_1
        b = self.set_2
        self.assertTrue(b in a | b)

    def test_inclusion_5(self):
        a = self.set_1
        ab = self.subset_1_2
        empty = self.empty_set
        self.assertTrue(ab - a == empty)

    def test_inclusion_6(self):
        a = self.set_1
        ab = self.subset_1_2
        self.assertTrue(-a in -ab)

    def test_relative_complement_1(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        self.assertTrue(c - (a & b) == (c - a) | (c - b))

    def test_relative_complement_2(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        self.assertTrue(c - (a | b) == (c - a) & (c - b))

    def test_relative_complement_3(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        self.assertTrue(c - (b - a) == (a & c) | (c - b))

    def test_relative_complement_4(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        self.assertTrue((b - a) & c == (b & c) - a)

    def test_relative_complement_5(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        self.assertTrue((b - a) & c == b & (c - a))

    def test_relative_complement_6(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        self.assertTrue((b - a) | c == (b | c) - (a - c))

    def test_relative_complement_7(self):
        a = self.set_1
        empty = self.empty_set
        self.assertTrue(a - a == empty)

    def test_relative_complement_8(self):
        a = self.set_1
        empty = self.empty_set
        self.assertTrue(empty - a == empty)

    def test_relative_complement_9(self):
        a = self.set_1
        empty = self.empty_set
        self.assertTrue(a - empty == a)

    def test_relative_complement_10(self):
        a = self.set_1
        b = self.set_2
        self.assertTrue(b - a == -a & b)

    def test_relative_complement_11(self):
        a = self.set_1
        b = self.set_2
        self.assertTrue(-(b - a) == a | (-b))

    def test_relative_complement_12(self):
        a = self.set_1
        universe = self.universe
        self.assertTrue(universe - a == -a)

    def test_relative_complement_13(self):
        a = self.set_1
        empty = self.empty_set
        universe = self.universe
        self.assertTrue(a - universe == empty)

    def test_inequality_0(self):
        a = self.set_1
        self.assertFalse(a != a)

    def test_ne(self):
        a = self.set_1
        self.assertTrue(-a != a)
