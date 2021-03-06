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
    return '{}{}'.format(letter, chr(ord('a') + integer))

class Test(TestCase):
    def setUp(self):
        self.pers = halftest.pers
        self.post = halftest.post
        self.today = halftest.today

        hexchars = 'abcdef'
        self.universe = self.pers()
        self.empty_set = -self.pers()
        self.c1 = hexchars[randint(0, len(hexchars) - 1)]
        self.c2 = hexchars[randint(0, len(hexchars) - 1)]
        self.c3 = hexchars[randint(0, len(hexchars) - 1)]
        self.set_1 = self.pers(last_name=('like', '{}%'.format(self.c1)))
        self.comp_set_1 = self.pers(
            last_name=('not like', '{}%'.format(self.c1)))
        self.set_2 = self.pers(last_name=('like', '_{}%'.format(self.c2)))
        self.subset_1_2 = self.pers(
            last_name=('like', '{}{}%'.format(self.c1, self.c2)))
        self.set_3 = self.pers(last_name=('like', '__{}%'.format(self.c3)))

    def and_test_1(self):
        a = self.set_1
        b = self.set_2
        (a & b)._mogrify()
        (a - (a - b))._mogrify()
        self.assertTrue(a & b == a - ( a - b))

    def and_test_2(self):
        a = self.set_1
        b = self.set_2
        (a & b)._mogrify()
        (((a | b) - (a - b) - ( b - a)))._mogrify()
        self.assertTrue(a & b == ((a | b) - (a - b) - ( b - a)))

    def and_test_3(self):
        a = self.set_1
        (a & a)._mogrify()
        a._mogrify()
        self.assertTrue(a & a == a)

    def and_test_4(self):
        a = self.set_1
        ab = self.subset_1_2
        (a & ab)._mogrify()
        ab._mogrify()
        self.assertTrue(a & ab == ab)

    def and_test_5(self):
        b = self.set_2
        ab = self.subset_1_2
        (b & ab)._mogrify()
        ab._mogrify()
        self.assertTrue(b & ab == ab)

    def and_test_6(self):
        a = self.set_1
        b = self.set_2
        ab = self.subset_1_2
        (a & b)._mogrify()
        ab._mogrify()
        self.assertTrue(a & b == ab)

    def and_absorbing_elt_test(self):
        a = self.set_1
        empty = self.empty_set
        (a & empty)._mogrify()
        empty._mogrify()
        self.assertTrue(a & empty == empty)
        self.assertTrue(len(empty) == 0)

    def and_neutral_elt_test(self):
        a = self.set_1
        universe = self.universe
        (universe & a)._mogrify()
        a._mogrify()
        self.assertTrue(universe & a == a)

    def or_test_1(self):
        a = self.set_1
        ab = self.subset_1_2
        (a | ab)._mogrify()
        a._mogrify()
        self.assertTrue(a | ab == a)

    def or_test_2(self):
        b = self.set_2
        ab = self.subset_1_2
        (b | ab)._mogrify()
        b._mogrify()
        self.assertTrue(b | ab == b)

    def or_neutral_elt_test(self):
        a = self.set_1
        empty = self.empty_set
        (a | empty)._mogrify()
        a._mogrify()
        self.assertTrue(a | empty == a)

    def or_absorbing_elt_test_1(self):
        a = self.set_1
        universe = self.universe
        (universe | a)._mogrify()
        universe._mogrify()
        self.assertTrue(universe | a == universe)

    def or_absorbing_elt_test_2(self):
        a = self.set_1
        universe = self.universe
        (a | universe)._mogrify()
        universe._mogrify()
        self.assertTrue(a | universe == universe)

    def or_absorbing_elt_test_3(self):
        empty = self.empty_set
        (empty | empty)._mogrify()
        empty._mogrify()
        self.assertTrue(empty | empty == empty)

    def not_test(self):
        a = self.set_1
        empty = self.empty_set
        (a - empty)._mogrify()
        a._mogrify()
        self.assertTrue(a - empty == a)

    def empty_test(self):
        a = self.set_1
        empty = self.empty_set
        (a - a)._mogrify()
        empty._mogrify()
        self.assertTrue(a - a == empty)

    def complementary_test_0(self):
        a = self.set_1
        comp_a = self.comp_set_1
        (-a)._mogrify()
        comp_a._mogrify()
        self.assertTrue(-a == comp_a)

    def complementary_test_1(self):
        a = self.set_1
        comp_a = self.comp_set_1
        universe = self.universe
        (a | comp_a)._mogrify()
        universe._mogrify()
        self.assertTrue(a | comp_a == universe)

    def complementary_test_2(self):
        a = self.set_1
        comp_a = self.comp_set_1
        (a - comp_a)._mogrify()
        a._mogrify()
        self.assertTrue(a - comp_a == a)

    def symetric_difference_test(self):
        a = self.set_1
        b = self.set_2
        ((a - b) | (b - a))._mogrify()
        ((a | b) - (a & b))._mogrify()
        self.assertTrue((a - b) | (b - a) == (a | b) - (a & b))

    def commutative_laws_test_1(self):
        a = self.set_1
        b = self.set_2
        (a & b)._mogrify()
        (b & a)._mogrify()
        self.assertTrue(a & b == b & a)

    def commutative_laws_test_2(self):
        a = self.set_1
        b = self.set_2
        (a | b)._mogrify()
        (b | a)._mogrify()
        self.assertTrue(a | b == b | a)

    def associative_laws_test_1(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        (a | (b | c))._mogrify()
        ((a | b) | c)._mogrify()
        self.assertTrue(a | (b | c) == (a | b) | c)

    def associative_laws_test_2(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        (a & (b & c))._mogrify()
        ((a & b) & c)._mogrify()
        self.assertTrue(a & (b & c) == (a & b) & c)

    def distributive_laws_test_1(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        (a | (b & c))._mogrify()
        ((a | b) & (a | c))._mogrify()
        self.assertTrue(a | (b & c) == (a | b) & (a | c))

    def distributive_laws_test_2(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        (a & (b | c))._mogrify()
        ((a & b) | (a & c))._mogrify()
        self.assertTrue(a & (b | c) == (a & b) | (a & c))

    def identity_laws_test_1(self):
        a = self.set_1
        empty = self.empty_set
        (a | empty)._mogrify()
        a._mogrify()
        self.assertTrue(a | empty == a)

    def identity_laws_test_2(self):
        a = self.set_1
        universe = self.universe
        (a & universe)._mogrify()
        a._mogrify()
        self.assertTrue(a & universe == a)

    def complement_laws_test_1(self):
        a = self.set_1
        comp_a = self.comp_set_1
        universe = self.universe
        (a | comp_a)._mogrify()
        universe._mogrify()
        self.assertTrue(a | comp_a == universe)

    def complement_laws_test_2(self):
        a = self.set_1
        comp_a = self.comp_set_1
        empty = self.empty_set
        (a & comp_a)._mogrify()
        empty._mogrify()
        self.assertTrue(a & comp_a == empty)

    def complement_laws_test_3(self):
        a = self.set_1
        universe = self.universe
        (a | (-a))._mogrify()
        universe._mogrify()
        self.assertTrue(a | (-a) == universe)

    def complement_laws_test_4(self):
        a = self.set_1
        empty = self.empty_set
        (a & (-a))._mogrify()
        empty._mogrify()
        self.assertTrue(a & (-a) == empty)

    def idempotent_laws_test_1(self):
        a = self.set_1
        (a | a)._mogrify()
        a._mogrify()
        self.assertTrue(a | a == a)

    def idempotent_laws_test_2(self):
        a = self.set_1
        (a & a)._mogrify()
        a._mogrify()
        self.assertTrue(a & a == a)

    def domination_laws_test_1(self):
        a = self.set_1
        universe = self.universe
        (a | universe)._mogrify()
        universe._mogrify()
        self.assertTrue(a | universe == universe)

    def domination_laws_test_2(self):
        a = self.set_1
        empty = self.empty_set
        (a & empty)._mogrify()
        empty._mogrify()
        self.assertTrue(a & empty == empty)

    def absorption_laws_test_1(self):
        a = self.set_1
        b = self.set_2
        (a | (a & b))._mogrify()
        a._mogrify()
        self.assertTrue(a | (a & b) == a)

    def absorption_laws_test_2(self):
        a = self.set_1
        b = self.set_2
        (a & (a | b))._mogrify()
        a._mogrify()
        self.assertTrue(a & (a | b) == a)

    def de_morgan_s_laws_test_1(self):
        a = self.set_1
        b = self.set_2
        ((-a) | (-b))._mogrify()
        (-(a & b))._mogrify()
        self.assertTrue((-a) | (-b) == -(a & b))

    def de_morgan_s_laws_test_2(self):
        a = self.set_1
        b = self.set_2
        (-(a | b))._mogrify()
        ((-a) & (-b))._mogrify()
        self.assertTrue(-(a | b) == (-a) & (-b))

    def double_complement_law_test(self):
        a = self.set_1
        (-(-a))._mogrify()
        a._mogrify()
        self.assertTrue(-(-a) == a)

    def empty_universe_complement_test(self):
        universe = self.universe
        empty = self.empty_set
        (-empty)._mogrify()
        universe._mogrify()
        self.assertTrue(-empty == universe)

    def inclusion_test_1_0(self):
        a = self.set_1
        a._mogrify()
        self.assertTrue(a in a)

    def inclusion_test_1_1(self):
        a = self.set_1
        ab = self.subset_1_2
        ab._mogrify()
        a._mogrify()
        self.assertTrue(ab in a)

    def inclusion_test_1_2(self):
        b = self.set_2
        ab = self.subset_1_2
        ab._mogrify()
        b._mogrify()
        self.assertTrue(ab in b)

    def ab_equal_a_inter_b_test(self):
        a = self.set_1
        b = self.set_2
        ab = self.subset_1_2
        ab._mogrify()
        (a & b)._mogrify()
        self.assertTrue(ab == a & b)

    def inclusion_test_2(self):
        a = self.set_1
        empty = self.empty_set
        empty._mogrify()
        a._mogrify()
        self.assertTrue(empty in a)

    def inclusion_test_3(self):
        a = self.set_1
        universe = self.universe
        a._mogrify()
        universe._mogrify()
        self.assertTrue(a in universe)

    def inclusion_test_4_1(self):
        a = self.set_1
        b = self.set_2
        a._mogrify()
        (a | b)._mogrify()
        self.assertTrue(a in a | b)

    def inclusion_test_4_2(self):
        a = self.set_1
        b = self.set_2
        b._mogrify()
        (a | b)._mogrify()
        self.assertTrue(b in a | b)

    def inclusion_test_5(self):
        a = self.set_1
        ab = self.subset_1_2
        empty = self.empty_set
        (ab - a)._mogrify()
        empty._mogrify()
        self.assertTrue(ab - a == empty)

    def inclusion_test_6(self):
        a = self.set_1
        ab = self.subset_1_2
        (-a)._mogrify()
        (-ab)._mogrify()
        self.assertTrue(-a in -ab)

    def relative_complement_test_1(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        (c - (a & b))._mogrify()
        ((c - a) | (c - b))._mogrify()
        self.assertTrue(c - (a & b) == (c - a) | (c - b))

    def relative_complement_test_2(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        (c - (a | b))._mogrify()
        ((c - a) & (c - b))._mogrify()
        self.assertTrue(c - (a | b) == (c - a) & (c - b))

    def relative_complement_test_3(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        (c - (b - a))._mogrify()
        ((a & c) | (c - b))._mogrify()
        self.assertTrue(c - (b - a) == (a & c) | (c - b))

    def relative_complement_test_4(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        ((b - a) & c)._mogrify()
        ((b & c) - a)._mogrify()
        self.assertTrue((b - a) & c == (b & c) - a)

    def relative_complement_test_5(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        ((b - a) & c)._mogrify()
        (b & (c - a))._mogrify()
        self.assertTrue((b - a) & c == b & (c - a))

    def relative_complement_test_6(self):
        a = self.set_1
        b = self.set_2
        c = self.set_3
        ((b - a) | c)._mogrify()
        ((b | c) - (a - c))._mogrify()
        self.assertTrue((b - a) | c == (b | c) - (a - c))

    def relative_complement_test_7(self):
        a = self.set_1
        empty = self.empty_set
        (a - a)._mogrify()
        empty._mogrify()
        self.assertTrue(a - a == empty)

    def relative_complement_test_8(self):
        a = self.set_1
        empty = self.empty_set
        (empty - a)._mogrify()
        empty._mogrify()
        self.assertTrue(empty - a == empty)

    def relative_complement_test_9(self):
        a = self.set_1
        empty = self.empty_set
        (a - empty)._mogrify()
        a._mogrify()
        self.assertTrue(a - empty == a)

    def relative_complement_test_10(self):
        a = self.set_1
        b = self.set_2
        (b - a)._mogrify()
        (-a & b)._mogrify()
        self.assertTrue(b - a == -a & b)

    def relative_complement_test_11(self):
        a = self.set_1
        b = self.set_2
        (-(b - a))._mogrify()
        (a | (-b))._mogrify()
        self.assertTrue(-(b - a) == a | (-b))

    def relative_complement_test_12(self):
        a = self.set_1
        universe = self.universe
        (universe - a)._mogrify()
        (-a)._mogrify()
        self.assertTrue(universe - a == -a)

    def relative_complement_test_13(self):
        a = self.set_1
        empty = self.empty_set
        universe = self.universe
        (a - universe)._mogrify()
        empty._mogrify()
        self.assertTrue(a - universe == empty)

    def inequality_test_0(self):
        a = self.set_1
        self.assertFalse(a != a)
