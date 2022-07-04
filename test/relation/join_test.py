#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from time import sleep
from random import randint
import psycopg2
import sys
from unittest import TestCase
from half_orm.hotest import HoTestCase

from ..init import halftest
from half_orm import relation_errors, model

class Test(HoTestCase):
    def setUp(self):
        self.pers = halftest.pers
        self.post = halftest.post
        self.comment = halftest.comment
        self.today = halftest.today
        self.post().delete(delete_all=True)
        self.comment().delete(delete_all=True)
        self.personne = self.pers(**next(self.pers(last_name='aa').select()))
        self.personne_ab = self.pers(**next(self.pers(last_name='ab').select()))
        post0 = self.post(title='post', content='essai')
        post0.author_last_name = self.personne.last_name
        post0.author_first_name = self.personne.first_name
        post0.author_birth_date = self.personne.birth_date
        self.post0 = post0.insert()[0]
        post1 = self.post(title="post 1", content="essai ab")
        post1.author_last_name = self.personne_ab.last_name
        post1.author_first_name = self.personne_ab.first_name
        post1.author_birth_date = self.personne_ab.birth_date
        self.post1 = post1.insert()[0]
        post2 = self.post(title="post 2", content="essai 2 ab")
        post2.author_last_name = self.personne_ab.last_name
        post2.author_first_name = self.personne_ab.first_name
        post2.author_birth_date = self.personne_ab.birth_date
        self.post2 = post2.insert()[0]
        self.comment_post = "comment post"
        self.comment_post_1 = "comment post 1"
        self.comment_ab_post = "comment ab post"
        self.comment_ab_post_1 = "comment ab post 1"
        self.comment_2_ab_post_1 = "comment 2 ab post 1"
        self.comment0 = self.comment(
            author_id=self.personne.id,
            post_id=self.post0['id'],
            content=self.comment_post).insert()[0]
        self.comment1 = self.comment(
            author_id=self.personne.id,
            post_id=self.post1['id'],
            content=self.comment_post_1).insert()[0]
        self.comment0_ab = self.comment(
            author_id=self.personne_ab.id,
            post_id=self.post0['id'],
            content=self.comment_ab_post).insert()[0]
        self.comment1_ab = self.comment(
            author_id=self.personne_ab.id,
            post_id=self.post1['id'],
            content=self.comment_ab_post_1).insert()[0]
        self.comment_2_1_ab = self.comment(
            author_id=self.personne_ab.id,
            post_id=self.post1['id'],
            content=self.comment_2_ab_post_1).insert()[0]
        self.res = self.personne.join(
            (self.comment(), 'comments'),
            (self.post(), 'posts')
        )[0]
        self.res1 = self.comment(content=self.comment_ab_post_1).join(
            (self.personne(), 'author', ['id', 'last_name']),
            (self.post(), 'post', 'title')
        )[0]

    def tearDown(self):
        self.post().delete(delete_all=True)
        self.comment().delete(delete_all=True)

    def test_join_without_fields(self):
        "should join the objects with all fields"
        comments = self.res['comments']
        posts = self.res['posts']
        self.assertTrue(isinstance(comments, list))
        self.assertTrue(isinstance(posts, list))
        self.assertEqual(posts[0]['id'], self.post0['id'])
        self.assertEqual(len(comments), 2)
        self.assertEqual(set(list(comments[0].keys())), set(list(self.comment()._fields)))
        comment_ids = {self.comment0['id'], self.comment1['id']}
        res_ids = {comments[0]['id'], comments[1]['id']}
        self.assertEqual(comment_ids, res_ids)

    def test_join_with_string(self):
        "join should return a list of values if fields is a string"
        self.assertIsInstance(self.res1['post'][0], str)
        self.assertEqual(self.res1['post'][0], 'post 1')

    def test_join_with_list(self):
        "join should return a list of dict if fields is a string"
        author = self.res1['author'][0]
        self.assertIsInstance(author, dict)
        self.assertEqual(author['last_name'], 'ab')
        self.assertEqual(set(list(author.keys())), {'id', 'last_name'})

    def test_join_should_work_with_FKEYS(self):
        "join should work with the use of FKEYS"
        author_ab = self.comment(content=self.comment_ab_post_1).author_
        res3 = author_ab.join(
            (self.comment(), 'comments', 'content')
        )[0]
        self.assertEqual(
          {self.comment_ab_post, self.comment_ab_post_1, self.comment_2_ab_post_1},
          set(res3['comments']))

    def test_join_with_constraint(self):
        "join should work with constraints on the joined objects"
        res = self.personne_ab.join(
            (self.comment(content=self.comment_ab_post_1), 'comments'),
            (self.post(), 'posts')
        )[0]
        print(res)
        comments = res['comments']
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0]['content'], self.comment_ab_post_1)

    def test_join_with_joined_object_with_FKEYS(self):
        "join should work with constraints on the joined objects"
        self.skipTest("Not implemented")
        print(halftest.post()._fkeys.keys())
        print(halftest.event._fkeys.keys())
        self.post().join((self.comment(), 'comments'))
        res = self.comment(content=self.comment_ab_post_1).join(
            (self.comment(content=self.comment_ab_post).post_, 'posts')
        )
        print(res)
        self.assertEqual('a', 'b')
