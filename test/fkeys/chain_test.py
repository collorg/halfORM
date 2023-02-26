#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

import random
from unittest import TestCase

from ..init import halftest

class Test(TestCase):
    "Fkeys chaining tests"
    def setUp(self):
        self.pers = halftest.Person()
        self.post = halftest.Post()
        self.comment = halftest.Comment()
        self.authors = []
        self.posts = []
        self.comments = []
        self.posts_by_author = {}
        self.authors_by_post = {}
        self.author_of_comment = {}
        self.comments_by_post = {}
        self.comments_by_author = {}
        self.author_comments_on_his_own_post = set()
        for author_idx in range(3):
            name = f'fkeys chain tester {author_idx}'
            self.authors.append(
                halftest.Person(last_name=name, first_name=name, birth_date='1970-01-01')
                .ho_insert())
        for post_idx in range(5):
            author_id = self.authors[random.randint(0, len(self.authors) - 1)]['id']
            title = f"test chaining post {post_idx} by {author_id}"
            self.posts.append(
                halftest.Person(id=author_id).post_rfk(title=title, content=title)
                .ho_insert())
            post_id = self.posts[-1]['id']
            if not post_id in self.authors_by_post:
                self.authors_by_post[post_id] = []
            self.authors_by_post[post_id].append(author_id)
            if not author_id in self.posts_by_author:
                self.posts_by_author[author_id] = []
            self.posts_by_author[author_id].append(post_id)
        for post in self.posts:
            for comment_idx in range(3):
                post_id = post['id']
                author_id = self.authors[random.randint(0, len(self.authors) - 1)]['id']
                content = f"test chaining comment {comment_idx} by {author_id} on {post['title']}"
                self.comments.append(
                    halftest.Post(id=post_id).comment_rfk(content=content, author_id=author_id)
                    .ho_insert())
                comment_id = self.comments[-1]['id']
                self.author_of_comment[comment_id] = author_id
                if not author_id in self.comments_by_author:
                    self.comments_by_author[author_id] = []
                self.comments_by_author[author_id].append(comment_id)
                if not post_id in self.comments_by_post:
                    self.comments_by_post[post_id] = []
                if author_id in self.authors_by_post[post_id]:
                    self.author_comments_on_his_own_post.add(comment_id)
                self.comments_by_post[post_id].append(comment_id)
        # print(self.authors_by_post)
        # print(self.posts_by_author)
        # print(self.author_of_comment)
        # print(self.comments_by_post)
        # print(self.comments_by_author)

    def tearDown(self):
        halftest.Person(last_name=('like', 'fkeys chain tester%')).ho_delete()

    def test_chain_person_post_comment(self):
        "it should be possible to chain from person to comment via post"
        self.assertTrue(isinstance(self.pers.post_rfk().comment_rfk(), halftest.Comment))

    def test_author_comments_on_his_own_post(self):
        "it should retreive the comments made on posts by the same author"
        nb_comments = 0
        for person in self.authors:
            person_id = person['id']
            person_first_name = person['first_name']
            comments = list(halftest.Person()
                .post_rfk(author_first_name=person_first_name)
                .comment_rfk(author_id=person_id))
            nb_comments += len(comments)
            for comment in comments:
                self.assertIn(comment['post_id'], self.posts_by_author[comment['author_id']])
                self.assertIn(comment['id'], self.author_comments_on_his_own_post)
        self.assertEqual(len(self.author_comments_on_his_own_post), nb_comments)

    def test_chain_post_comment_author(self):
        "it should be possible to chain from post to author via comment"
        self.assertTrue(isinstance(self.post.comment_rfk().author_fk(), halftest.Person))

    def test_chain_comment_post_author(self):
        "it should be possible to chain from comment to author via post"
        self.assertTrue(isinstance(self.comment().post_fk().author_fk(), halftest.Person))
