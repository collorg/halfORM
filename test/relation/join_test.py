#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

import sys
from pprint import PrettyPrinter
from time import sleep
from random import randint
from unittest import TestCase
from half_orm.hotest import HoTestCase

import psycopg2

from ..init import halftest
from half_orm import relation_errors, model

POST1 = 'post 1'

class Test(HoTestCase):
    def setUp(self):
        self.pers = halftest.person_cls()
        self.post = halftest.post_cls()
        self.comment = halftest.comment_cls()
        self.blog_view = halftest.blog_view_cls()
        self.today = halftest.today
        self.post().ho_delete(delete_all=True)
        self.comment().ho_delete(delete_all=True)
        self.personne = self.pers(**next(self.pers(last_name='aa')))
        self.personne_ab = self.pers(**next(self.pers(last_name='ab')))
        post0 = self.post(title='post', content='essai')
        post0.author_last_name = self.personne.last_name
        post0.author_first_name = self.personne.first_name
        post0.author_birth_date = self.personne.birth_date
        self.post0 = post0.ho_insert('id')
        post1 = self.post(title="post 1", content="essai ab")
        post1.author_last_name = self.personne_ab.last_name
        post1.author_first_name = self.personne_ab.first_name
        post1.author_birth_date = self.personne_ab.birth_date
        self.post1 = post1.ho_insert('id')
        post2 = self.post(title="post 2", content="essai 2 ab")
        post2.author_last_name = self.personne_ab.last_name
        post2.author_first_name = self.personne_ab.first_name
        post2.author_birth_date = self.personne_ab.birth_date
        self.post2 = post2.ho_insert('title')
        self.comment_post = "comment post"
        self.comment_post_1 = "comment post 1"
        self.comment_ab_post = "comment ab post"
        self.comment_ab_post_1 = "comment ab post 1"
        self.comment_2_ab_post_1 = "comment 2 ab post 1"
        self.comment0 = self.comment(
            author_id=self.personne.id,
            post_id=self.post0['id'],
            content=self.comment_post).ho_insert()
        self.comment1 = self.comment(
            author_id=self.personne.id,
            post_id=self.post1['id'],
            content=self.comment_post_1).ho_insert()
        self.comment0_ab = self.comment(
            author_id=self.personne_ab.id,
            post_id=self.post0['id'],
            content=self.comment_ab_post).ho_insert()
        self.comment1_ab = self.comment(
            author_id=self.personne_ab.id,
            post_id=self.post1['id'],
            content=self.comment_ab_post_1).ho_insert()
        self.comment_2_1_ab = self.comment(
            author_id=self.personne_ab.id,
            post_id=self.post1['id'],
            content=self.comment_2_ab_post_1).ho_insert()
        self.res = self.personne.ho_join(
            (self.comment(), 'comments'),
            (self.post(), 'posts')
        )[0]
        self.res1 = self.comment(content=self.comment_ab_post_1).ho_join(
            (self.personne(), 'author', ['id', 'last_name']),
            (self.post(), 'post', 'title')
        )[0]

    def tearDown(self):
        self.post().ho_delete(delete_all=True)
        self.comment().ho_delete(delete_all=True)
        halftest.model.execute_query("drop table if exists tree")

    def test_join_without_fields(self):
        "should join the objects with all fields"
        comments = self.res['comments']
        posts = self.res['posts']
        self.assertIsInstance(comments, list)
        self.assertIsInstance(posts, list)
        self.assertEqual(posts[0]['id'], self.post0['id'])
        self.assertEqual(len(comments), 2)
        self.assertEqual(set(list(comments[0].keys())), set(list(self.comment()._ho_fields)))
        comment_ids = {self.comment0['id'], self.comment1['id']}
        res_ids = {comments[0]['id'], comments[1]['id']}
        self.assertEqual(comment_ids, res_ids)

    def test_join_with_string(self):
        "ho_join should return a list of values if fields is a string"
        self.assertIsInstance(self.res1['post'][0], str)
        self.assertEqual(self.res1['post'][0], POST1)

    def test_join_with_list(self):
        "ho_join should return a list of dict if fields is a string"
        author = self.res1['author'][0]
        self.assertIsInstance(author, dict)
        self.assertEqual(author['last_name'], 'ab')
        self.assertEqual(set(list(author.keys())), {'id', 'last_name'})

    def test_join_should_work_with_FKEYS(self):
        "ho_join should work with the use of FKEYS"
        author_ab = self.comment(content=self.comment_ab_post_1).author_fk()
        res3 = author_ab.ho_join(
            (self.comment(), 'comments', 'content')
        )[0]
        self.assertEqual(
          {self.comment_ab_post, self.comment_ab_post_1, self.comment_2_ab_post_1},
          set(res3['comments']))

    def test_join_with_constraint(self):
        "ho_join should work with constraints on the joined objects"
        res = self.personne_ab.ho_join(
            (self.comment(content=self.comment_ab_post_1), 'comments'),
            (self.post(), 'posts')
        )[0]
        comments = res['comments']
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0]['content'], self.comment_ab_post_1)

        comments_by_posts = self.post().ho_join((self.comment(), 'comments'))
        ESSAI = 'essai'
        ESSAI_AB = 'essai ab'
        count = {ESSAI: 2, ESSAI_AB: 3}
        if comments_by_posts[0]['content'] == ESSAI:
            self.assertEqual(len(comments_by_posts[0]['comments']), count[ESSAI])
            self.assertEqual(len(comments_by_posts[1]['comments']), count[ESSAI_AB])
        else:
            self.assertEqual(len(comments_by_posts[0]['comments']), count[ESSAI_AB])
            self.assertEqual(len(comments_by_posts[1]['comments']), count[ESSAI])

        comments_by_post = self.post().ho_join((self.comment(content=self.comment_post), 'comments'))
        self.assertEqual(len(comments_by_post), 1)
        self.assertEqual(comments_by_post[0]['title'], 'post')
        self.assertEqual(len(comments_by_post[0]['comments']), 1)
        self.assertEqual(comments_by_post[0]['comments'][0]['content'], self.comment_post)

        comments_by_post_1 = self.post().ho_join((self.comment(content=self.comment_ab_post_1), 'comments'))
        self.assertEqual(len(comments_by_post_1), 1)
        self.assertEqual(comments_by_post_1[0]['title'], POST1)
        self.assertEqual(len(comments_by_post_1[0]['comments']), 1)
        self.assertEqual(comments_by_post_1[0]['comments'][0]['content'], self.comment_ab_post_1)


    def test_join_with_joined_object_with_FKEYS(self):
        "ho_join should work with constraints on the joined objects"

        post_by_comment = self.comment(content=self.comment_post).ho_join(
            (self.comment(content=self.comment_post).post_fk(), 'post')
        )
        self.assertEqual(len(post_by_comment), 1)
        self.assertEqual(post_by_comment[0]['content'], self.comment_post)
        self.assertEqual(len(post_by_comment[0]['post']), 1)
        self.assertEqual(post_by_comment[0]['post'][0]['title'], 'post')

        post_by_comment_ab_post_1 = self.comment(content=self.comment_ab_post_1).ho_join(
            (self.comment(content=self.comment_ab_post_1).post_fk(), 'post')
        )
        self.assertEqual(len(post_by_comment_ab_post_1), 1)
        self.assertEqual(post_by_comment_ab_post_1[0]['content'], self.comment_ab_post_1)
        self.assertEqual(len(post_by_comment_ab_post_1[0]['post']), 1)
        self.assertEqual(post_by_comment_ab_post_1[0]['post'][0]['title'], POST1)

    def test_join_error_1(self):
        "f_rels should be tuples"
        with self.assertRaises(RuntimeError) as exc:
            self.comment().ho_join(
                self.personne(),
                (self.post(), 'post', 'title')
            )
        self.assertEqual(str(exc.exception), 'f_rels must be a list of tuples.')

    def test_join_error_2(self):
        "f_rels should have 2 or 3 arguments"
        with self.assertRaises(RuntimeError) as exc:
            self.comment().ho_join(
                (self.personne(), ),
                (self.post(), 'post', 'title')
            )
        self.assertEqual(str(exc.exception), 'f_rel must have 2 or 3 arguments. Got 1.')

    def test_join_error_3(self):
        with self.assertRaises(RuntimeError) as exc:
            self.comment().ho_join(
                (self.blog_view(), 'post'),
                (self.post(), 'post', 'title')
            )
        self.assertEqual(str(exc.exception), 'No foreign key between "halftest":"blog"."comment" and "halftest":"blog.view"."post_comment"!')

    def test_join_error_with_itself(self):
        halftest.model.execute_query("create table tree (id text primary key, parent text references tree(id))")
        halftest.model.reconnect(reload=True)
        Tree = halftest.model.get_relation_class('public.tree')
        with self.assertRaises(RuntimeError) as exc:
            tree = Tree()
            tree._ho_fkeys['tree_parent_fkey'].set(tree)
            list(tree)
        self.assertEqual(str(exc.exception), "Can't set Fkey tree_parent_fkey on the same object")
