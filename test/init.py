#!/usr/bin/env python3

import os
import sys
from datetime import date
from half_orm.model import Model

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

model = Model(config_file='{}/halftest.ini'.format(path), scope="halftest")

def name(letter, integer):
    return '{}{}'.format(letter, chr(ord('a') + integer))

class HalfTest:
    def __init__(self):
        assert model._scope == "halftest"
        self.dbname = model._dbname
        self.today = date.today()
        self.pers = model._import_class("actor.person")()
        self.relation = model._import_class
        self.post = model._import_class("blog.post")()
        self.comment = model._import_class("blog.comment")()
        self.event = model._import_class("blog.event")()

        @self.pers.Transaction
        def insert_pers(pers):
            for n in 'abcdef':
                for i in range(10):
                    last_name = name(n, i)
                    first_name = name(n, i)
                    birth_date = self.today
                    self.pers(
                        last_name=last_name,
                        first_name=first_name,
                        birth_date=birth_date).insert()

        if len(self.pers) != 60:
            self.pers.delete(delete_all=True)
            self.post.delete(delete_all=True)
            insert_pers(self.pers)

try:
    halftest = HalfTest()
except Exception as err:
    sys.stderr.write('{}\n'.format(err))
    sys.stderr.write(README.format(path))
    sys.exit(1)
