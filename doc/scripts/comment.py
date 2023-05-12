#!/usr/bin/env python

import sys
from half_orm.model import Model
from person import Person

halftest = Model('halftest')

class Post(halftest.get_relation_class('blog.post')):
    Fkeys = {
        'comments_rfk': '_reverse_fkey_halftest_blog_comment_post_id',
        'author_fk': 'author',
    }

class Comment(halftest.get_relation_class('blog.comment')):
    Fkeys = {
        'post_fk': 'post',
        'author_fk': 'author',
    }

print(Comment().post_fk)
comment = Comment()
comment.post_fk.set(Post(title='true'))
print(list(comment.ho_select()))

gaston = Person(last_name=('ilike', 'Lagaffe'), first_name='Gaston', birth_date='1957-02-28')
if len(gaston) == 0:
    gaston.ho_insert()

post = Post(title='Essai', content='Pas mieux...')
post.author_fk.set(gaston)
if len(post) == 0:
    print(post.ho_insert())

post = Post(**list(post.ho_select())[0])

comment = Comment(content = 'Et là ça fonctionne ?')
comment.post_fk.set(post)
comment.author_fk.set(gaston)
if len(comment) == 0:
    print(comment.ho_insert())

comment = Comment(content = "C'est pourtant simple...")
comment.post_fk.set(post)
comment.author_fk.set(gaston)
if len(comment) == 0:
    print(comment.ho_insert())

gaston_comments = gaston.comments_rfk(content=('ilike', '%simple%'))
print(list(gaston_comments))

# print(Post())
