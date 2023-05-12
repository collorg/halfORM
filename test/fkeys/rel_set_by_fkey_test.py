#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from half_orm.hotest import HoTestCase
from unittest import skip

from ..init import halftest

class Test(HoTestCase):
    def setUp(self):
        self.pers = halftest.Person()
        self.post = halftest.Post()

    def test_just_fkey_set(self):
        "it should pass"
        gaston = halftest.Person(last_name='Lagaffe')
        posts = gaston.post_rfk()
        posts.ho_limit = 1
        # posts.ho_mogrify()
        list(posts.ho_select())

    @skip
    def test_just_fkey_set_delete(self):
        "it should pass"
        gaston = halftest.Person(last_name='Lagaffe')
        posts = gaston.post_rfk()
        posts.ho_mogrify()
        print('XXX ICI')
        posts.ho_delete()
    