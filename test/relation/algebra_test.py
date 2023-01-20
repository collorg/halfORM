#!/usr/bin/env python
#-*- coding:  utf-8 -*-

from random import randint
import psycopg2
import sys
from unittest import TestCase
from datetime import date

from ..init import halftest
from half_orm import relation_errors, model

def name(letter, integer):
    return f"{letter}{chr(ord('a') + integer)}"

class Test(TestCase):
    def setUp(self):
        self.pers = halftest.Person()
        self.post = halftest.Post()
        self.today = halftest.today

        hexchars = 'abcdef'
        self.universe = self.pers()
        self.empty_set = -self.pers()
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

    def test_and_1(self):
        a = self.set_1
        b = self.set_2
        (a & b)._ho_mogrify()
        (a - (a - b))._ho_mogrify()
        self.assertTrue(a & b == a - ( a - b))

    def test_and_2(self):
        a = self.set_1
        b = self.set_2
        (a & b)._ho_mogrify()
        (((a | b) - (a - b) - ( b - a)))._ho_mogrify()
        self.assertTrue(a & b == ((a | b) - (a - b) - ( b - a)))

    def test_and_3(self):
        a = self.set_1
        (a & a)._ho_mogrify()
        a._ho_mogrify()
        self.assertTrue(a & a == a)

    def test_and_4(self):
        a = self.set_1
        ab = self.subset_1_2
        (a & ab)._ho_mogrify()
        ab._ho_mogrify()
        self.assertTrue(a & ab == ab)

    def test_and_5(self):
        b = self.set_2
        ab = self.subset_1_2
        (b & ab)._ho_mogrify()
        ab._ho_mogrify()
        self.assertTrue(b & ab == ab)

    def test_and_6(self):
        a = self.set_1
        b = self.set_2
        ab = self.subset_1_2
        (a & b)._ho_mogrify()
        ab._ho_mogrify()
        self.assertTrue(a & b == ab)

    def test_and_absorbing_elt(self):
        a = self.set_1
        empty = self.empty_set
        (a & empty)._ho_mogrify()
        empty._ho_mogrify()
        self.assertTrue(a & empty == empty)
        self.assertTrue(empty.ho_is_empty())

    def test_and_neutral_elt(self):
        a = self.set_1
        universe = self.universe
        (universe & a)._ho_mogrify()
        a._ho_mogrify()
        self.assertTrue(universe & a == a)

    def test_or_1(self):
        a = self.set_1
        ab = self.subset_1_2
        (a | ab)._ho_mogrify()
        a._ho_mogrify()
        self.assertTrue(a | ab == a)

    def test_or_2(self):
        b = self.set_2
        ab = self.subset_1_2
        (b | ab)._ho_mogrify()
        b._ho_mogrify()
        self.assertTrue(b | ab == b)

    def test_or_neutral_elt(self):
        a = self.set_1
        empty = self.empty_set
        (a | empty)._ho_mogrify()
        a._ho_mogrify()
        self.assertTrue(a | empty == a)

    def test_or_absorbing_elt_1(self):
        a = self.set_1
        universe = self.universe
        (universe | a)._ho_mogrify()
        universe._ho_mogrify()
        self.assertTrue(universe | a == universe)

    def test_or_absorbing_elt_2(self):
        a = self.set_1
        universe = self.universe
        (a | universe)._ho_mogrify()
        universe._ho_mogrify()
        self.assertTrue(a | universe == universe)

    def test_or_absorbing_elt_3(self):
        empty = self.empty_set
        (empty | empty)._ho_mogrify()
        empty._ho_mogrify()
        self.assertTrue(empty | empty == empty)

    def test_not(self):
        a = self.set_1
        empty = self.empty_set
        (a - empty)._ho_mogrify()
        a._ho_mogrify()
        self.assertTrue(a - empty == a)

    def test_empty(self):
        a = self.set_1
        empty = self.empty_set
        (a - a)._ho_mogrify()
        empty._ho_mogrify()
        self.assertTrue(a - a == empty)

    def test_complementary_0(self):
        a = self.set_1
        comp_a = self.comp_set_1
        (-a)._ho_mogrify()
        comp_a._ho_mogrify()
        self.assertTrue(-a == comp_a)

    def test_complementary_1(self):
        a = self.set_1
        comp_a = self.comp_set_1
        universe = self.universe
        (a | comp_a)._ho_mogrify()
        universe._ho_mogrify()
        self.assertTrue(a | comp_a == universe)

    def test_complementary_2(self):
        a = self.set_1
        comp_a = self.comp_set_1
        (a - comp_a)._ho_mogrify()
        a._ho_mogrify()
        self.assertTrue(a - comp_a == a)

    def test_symetric_difference(self):
        a = self.set_1
        b = self.set_2
        ((a - b) | (b - a))._ho_mogrify()
        ((a | b) - (a & b))._ho_mogrify()
        self.assertTrue((a - b) | (b - a) == (a | b) - (a & b))

    def test_commutative_laws_1(self):
        a = self.set_1
        b = self.set_2
        (a & b)._ho_mogrify()
        (b & a)._ho_mogrify()
        self.assertTrue(a & b == b & a)

    def test_commutative_laws_2(self):
        a = self.set_1
        b = self.set_2
        (a | b)._ho_mogrify()
        (b | a)._ho_mogrify()
        self.assertTrue(a | b == b | a)

    def test_associative_laws_1(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        (a | (b | c))._ho_mogrify()
        ((a | b) | c)._ho_mogrify()
        self.assertTrue(a | (b | c) == (a | b) | c)

    def test_associative_laws_2(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        (a & (b & c))._ho_mogrify()
        ((a & b) & c)._ho_mogrify()
        self.assertTrue(a & (b & c) == (a & b) & c)

    def test_distributive_laws_1(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        (a | (b & c))._ho_mogrify()
        ((a | b) & (a | c))._ho_mogrify()
        self.assertTrue(a | (b & c) == (a | b) & (a | c))

    def test_distributive_laws_2(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        (a & (b | c))._ho_mogrify()
        ((a & b) | (a & c))._ho_mogrify()
        self.assertTrue(a & (b | c) == (a & b) | (a & c))

    def test_identity_laws_1(self):
        a = self.set_1
        empty = self.empty_set
        (a | empty)._ho_mogrify()
        a._ho_mogrify()
        self.assertTrue(a | empty == a)

    def test_identity_laws_2(self):
        a = self.set_1
        universe = self.universe
        (a & universe)._ho_mogrify()
        a._ho_mogrify()
        self.assertTrue(a & universe == a)

    def test_complement_laws_1(self):
        a = self.set_1
        comp_a = self.comp_set_1
        universe = self.universe
        (a | comp_a)._ho_mogrify()
        universe._ho_mogrify()
        self.assertTrue(a | comp_a == universe)

    def test_complement_laws_2(self):
        a = self.set_1
        comp_a = self.comp_set_1
        empty = self.empty_set
        (a & comp_a)._ho_mogrify()
        empty._ho_mogrify()
        self.assertTrue(a & comp_a == empty)

    def test_complement_laws_3(self):
        a = self.set_1
        universe = self.universe
        (a | (-a))._ho_mogrify()
        universe._ho_mogrify()
        self.assertTrue(a | (-a) == universe)

    def test_complement_laws_4(self):
        a = self.set_1
        empty = self.empty_set
        (a & (-a))._ho_mogrify()
        empty._ho_mogrify()
        self.assertTrue(a & (-a) == empty)

    def test_idempotent_laws_1(self):
        a = self.set_1
        (a | a)._ho_mogrify()
        a._ho_mogrify()
        self.assertTrue(a | a == a)

    def test_idempotent_laws_2(self):
        a = self.set_1
        (a & a)._ho_mogrify()
        a._ho_mogrify()
        self.assertTrue(a & a == a)

    def test_domination_laws_1(self):
        a = self.set_1
        universe = self.universe
        (a | universe)._ho_mogrify()
        universe._ho_mogrify()
        self.assertTrue(a | universe == universe)

    def test_domination_laws_2(self):
        a = self.set_1
        empty = self.empty_set
        (a & empty)._ho_mogrify()
        empty._ho_mogrify()
        self.assertTrue(a & empty == empty)

    def test_absorption_laws_1(self):
        a = self.set_1
        b = self.set_2
        (a | (a & b))._ho_mogrify()
        a._ho_mogrify()
        self.assertTrue(a | (a & b) == a)

    def test_absorption_laws_2(self):
        a = self.set_1
        b = self.set_2
        (a & (a | b))._ho_mogrify()
        a._ho_mogrify()
        self.assertTrue(a & (a | b) == a)

    def test_de_morgan_s_laws_1(self):
        a = self.set_1
        b = self.set_2
        ((-a) | (-b))._ho_mogrify()
        (-(a & b))._ho_mogrify()
        self.assertTrue((-a) | (-b) == -(a & b))

    def test_de_morgan_s_laws_2(self):
        a = self.set_1
        b = self.set_2
        (-(a | b))._ho_mogrify()
        ((-a) & (-b))._ho_mogrify()
        self.assertTrue(-(a | b) == (-a) & (-b))

    def test_double_complement_law(self):
        a = self.set_1
        (-(-a))._ho_mogrify()
        a._ho_mogrify()
        self.assertTrue(-(-a) == a)

    def test_empty_universe_complement(self):
        universe = self.universe
        empty = self.empty_set
        (-empty)._ho_mogrify()
        universe._ho_mogrify()
        self.assertTrue(-empty == universe)

    def test_inclusion_1_0(self):
        a = self.set_1
        a._ho_mogrify()
        self.assertTrue(a in a)

    def test_inclusion_1_1(self):
        a = self.set_1
        ab = self.subset_1_2
        ab._ho_mogrify()
        a._ho_mogrify()
        self.assertTrue(ab in a)

    def test_inclusion_1_2(self):
        b = self.set_2
        ab = self.subset_1_2
        ab._ho_mogrify()
        b._ho_mogrify()
        self.assertTrue(ab in b)

    def test_ab_equal_a_inter_b(self):
        a = self.set_1
        b = self.set_2
        ab = self.subset_1_2
        ab._ho_mogrify()
        (a & b)._ho_mogrify()
        self.assertTrue(ab == a & b)

    def test_inclusion_2(self):
        a = self.set_1
        empty = self.empty_set
        empty._ho_mogrify()
        a._ho_mogrify()
        self.assertTrue(empty in a)

    def test_inclusion_3(self):
        a = self.set_1
        universe = self.universe
        a._ho_mogrify()
        universe._ho_mogrify()
        self.assertTrue(a in universe)

    def test_inclusion_4_1(self):
        a = self.set_1
        b = self.set_2
        a._ho_mogrify()
        (a | b)._ho_mogrify()
        self.assertTrue(a in a | b)

    def test_inclusion_4_2(self):
        a = self.set_1
        b = self.set_2
        b._ho_mogrify()
        (a | b)._ho_mogrify()
        self.assertTrue(b in a | b)

    def test_inclusion_5(self):
        a = self.set_1
        ab = self.subset_1_2
        empty = self.empty_set
        (ab - a)._ho_mogrify()
        empty._ho_mogrify()
        self.assertTrue(ab - a == empty)

    def test_inclusion_6(self):
        a = self.set_1
        ab = self.subset_1_2
        (-a)._ho_mogrify()
        (-ab)._ho_mogrify()
        self.assertTrue(-a in -ab)

    def test_relative_complement_1(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        (c - (a & b))._ho_mogrify()
        ((c - a) | (c - b))._ho_mogrify()
        self.assertTrue(c - (a & b) == (c - a) | (c - b))

    def test_relative_complement_2(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        (c - (a | b))._ho_mogrify()
        ((c - a) & (c - b))._ho_mogrify()
        self.assertTrue(c - (a | b) == (c - a) & (c - b))

    def test_relative_complement_3(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        (c - (b - a))._ho_mogrify()
        ((a & c) | (c - b))._ho_mogrify()
        self.assertTrue(c - (b - a) == (a & c) | (c - b))

    def test_relative_complement_4(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        ((b - a) & c)._ho_mogrify()
        ((b & c) - a)._ho_mogrify()
        self.assertTrue((b - a) & c == (b & c) - a)

    def test_relative_complement_5(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        ((b - a) & c)._ho_mogrify()
        (b & (c - a))._ho_mogrify()
        self.assertTrue((b - a) & c == b & (c - a))

    def test_relative_complement_6(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        ((b - a) | c)._ho_mogrify()
        ((b | c) - (a - c))._ho_mogrify()
        self.assertTrue((b - a) | c == (b | c) - (a - c))

    def test_relative_complement_7(self):
        a = self.set_1
        empty = self.empty_set
        (a - a)._ho_mogrify()
        empty._ho_mogrify()
        self.assertTrue(a - a == empty)

    def test_relative_complement_8(self):
        a = self.set_1
        empty = self.empty_set
        (empty - a)._ho_mogrify()
        empty._ho_mogrify()
        self.assertTrue(empty - a == empty)

    def test_relative_complement_9(self):
        a = self.set_1
        empty = self.empty_set
        (a - empty)._ho_mogrify()
        a._ho_mogrify()
        self.assertTrue(a - empty == a)

    def test_relative_complement_10(self):
        a = self.set_1
        b = self.set_2
        (b - a)._ho_mogrify()
        (-a & b)._ho_mogrify()
        self.assertTrue(b - a == -a & b)

    def test_relative_complement_11(self):
        a = self.set_1
        b = self.set_2
        (-(b - a))._ho_mogrify()
        (a | (-b))._ho_mogrify()
        self.assertTrue(-(b - a) == a | (-b))

    def test_relative_complement_12(self):
        a = self.set_1
        universe = self.universe
        (universe - a)._ho_mogrify()
        (-a)._ho_mogrify()
        self.assertTrue(universe - a == -a)

    def test_relative_complement_13(self):
        a = self.set_1
        empty = self.empty_set
        universe = self.universe
        (a - universe)._ho_mogrify()
        empty._ho_mogrify()
        self.assertTrue(a - universe == empty)

    def test_inequality_0(self):
        a = self.set_1
        self.assertFalse(a != a)
