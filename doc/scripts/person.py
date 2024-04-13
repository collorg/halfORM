#!/usr/bin/env python

import sys
from half_orm.model import Model

halftest = Model('halftest')

"""
"""

class Person(halftest.get_relation_class('actor.person')):
    """Class to deal with the data in the actor.person table.
    Use `print(Person())` to get more information on the actor.person table. 
    """
    Fkeys = {
        'comments_rfk': '_reverse_fkey_halftest_blog_comment_author_id',
        'events_rfk': '_reverse_fkey_halftest_blog_event_author_first_name_author_last_name_author_birth_date',
        'post_rfk': '_reverse_fkey_halftest_blog_post_author_first_name_author_last_name_author_birth_date',
    }

    def insert_many(self, *data):
        "insert many people in a single transaction"
        @self.ho_transaction
        def insert(self, *data):
            for d_pers in data:
                self(**d_pers).ho_insert()
        insert(self, *data)


    def upper_last_name(self):
        "tranform last name to upper case."
        @self.ho_transaction
        def update(self):
            for d_pers in self.ho_select('id', 'last_name'):
                pers = Person(**d_pers)
                pers.ho_update(last_name=d_pers['last_name'].upper())

        update(self)

if __name__ == '__main__':
    people = Person()

    people.ho_delete(delete_all=True)
    Person(**{'last_name':'Jourdan', 'first_name':'Gil', 'birth_date':'1956-09-20'}).ho_insert()
    try:
        people.insert_many(*[
            {'last_name':'Lagaffe', 'first_name':'Gaston', 'birth_date':'1957-02-28'},
            {'last_name':'Fricotin', 'first_name':'Bibi', 'birth_date':'1924-10-05'},
            {'last_name':'Maltese', 'first_name':'Corto', 'birth_date':'1975-01-07'},
            {'last_name':'Talon', 'first_name':'Achile', 'birth_date':'1963-11-07'},
            {'last_name':'Jourdan', 'first_name':'Gil', 'birth_date':'1956-09-20'}
        ])
    except Exception as err:
        print(err)

    print(list(people.ho_select()))

    people.ho_offset(1).ho_limit(2)
    print([dict(elt) for elt in list(people.ho_select())])

    print([dict(elt) for elt in list(people.ho_select('last_name'))])

    a_pers = Person(last_name = ('ilike', '_a%'))
    print([elt['last_name'] for elt in a_pers.ho_select('last_name')])
    a_pers.upper_last_name()
    print([elt['last_name'] for elt in a_pers.ho_select('last_name')])
