#!/usr/bin/env python3

import os
import sys
from datetime import date
from half_orm.model import Model
from half_orm.relation import singleton

path = os.path.dirname(__file__)
sys.path.insert(0, f'{path}/halftest')

README = """
Create the database halftest First:
- psql template1 -f {}/sql/halftest.sql
This command will create:
- a user halftest.
  When prompted for the password type: halftest
- a database halftest

To drop halftest database and user when you're done with the tests:
- dropdb halftest; dropuser halftest
"""

model = Model('halftest', scope="halftest")
model2 = Model('hop_test')

HALFTEST_STR = '''r "actor"."person"
r "blog"."comment"
r "blog"."event"
r "blog"."post"
v "blog.view"."post_comment"'''

HALFTEST_REL_LISTS = [
    ('r', ('halftest', 'actor', 'person')),
    ('r', ('halftest', 'blog', 'comment')),
    ('r', ('halftest', 'blog', 'event')),
    ('r', ('halftest', 'blog', 'post')),
    ('r', ('halftest', 'half_orm_meta', 'hop_release')),
    ('r', ('halftest', 'half_orm_meta', 'hop_release_issue')),
    ('v', ('halftest', 'blog.view', 'post_comment')),
    ('v', ('halftest', 'half_orm_meta.view', 'hop_last_release')),
    ('v', ('halftest', 'half_orm_meta.view', 'hop_penultimate_release'))
]

HALFTEST_DESC = [
    ('r', ('halftest', 'actor', 'person'), []),
    ('r', ('halftest', 'blog', 'comment'), []),
    ('r', ('halftest', 'blog', 'event'), [('halftest', 'blog', 'post')]),
    ('r', ('halftest', 'blog', 'post'), []),
    ('v', ('halftest', 'blog.view', 'post_comment'), [])
]

GASTON = {
    'last_name': 'Lagaffe', 'first_name': 'Gaston', 'birth_date': date.today()
}

def name(letter, integer):
    return f"{letter}{chr(ord('a') + integer)}"

class HalfTest:
    def __init__(self):
        self.model = model
        self.model2 = model2
        assert model._scope == "halftest"
        self.dbname = model._dbname
        self.today = date.today()
        self.Person = model._import_class("actor.person")
        self.Person().ho_delete(delete_all=True)
        self.Post = model._import_class("blog.post")
        self.Comment = model._import_class("blog.comment")
        self.Event = model._import_class("blog.event")
        self.BlogView = model._import_class("blog.view.post_comment")
        class PC(self.Person):
            def last_name(self):
                pass

        self.PublicA = model2.get_relation_class('public.a')
        self._person = self.Person()
        self.gaston = self.Person(**GASTON)
        self.pc = PC()
        self.relation = model._import_class

        @self._person.ho_transaction
        def init_pers(pers):
            sys.stderr.write('Initializing actor.person\n')
            self.Person().ho_delete(delete_all=True)
            self.Post().ho_delete(delete_all=True)
            for letter in 'abcdef':
                for i in range(10):
                    last_name = name(letter, i)
                    first_name = name(letter, i)
                    birth_date = self.today
                    pers(
                        last_name=last_name,
                        first_name=first_name,
                        birth_date=birth_date).ho_insert()

        if len(self.Person()) != 60:
            init_pers(self.Person())

halftest = HalfTest()
