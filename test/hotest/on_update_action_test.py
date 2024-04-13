#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

from half_orm.hotest import HoTestCase

from ..init import halftest

CONST = 'b_a_fkey'
DROP_CONST = f'alter table tmp.b drop constraint {CONST}'

class Test(HoTestCase):
    def setUp(self):
        halftest.model.execute_query('create schema if not exists tmp');
        halftest.model.execute_query('create table if not exists tmp.a(a text primary key)')
        halftest.model.execute_query('create table if not exists tmp.b(a text references tmp.a)')
        halftest.model.reconnect(reload=True)
        self.RelA = halftest.model.get_relation_class('tmp.a')
        self.RelB = halftest.model.get_relation_class('tmp.b')

    def tearDown(self):
        halftest.model.execute_query('drop schema tmp cascade')
        halftest.model.reconnect(reload=True)

    def test_no_action(self):
        self.hotAssertOnUpdateNoAction(self.RelA, '_reverse_fkey_halftest_tmp_b_a')

    def test_restrict(self):
        halftest.model.execute_query(DROP_CONST)
        halftest.model.execute_query('alter table tmp.b add constraint b_a_fkey foreign key(a) references tmp.a on update restrict')
        halftest.model.reconnect(reload=True)
        self.hotAssertOnUpdateRestict(self.RelB, CONST)

    def test_cascade(self):
        halftest.model.execute_query(DROP_CONST)
        halftest.model.execute_query('alter table tmp.b add constraint b_a_fkey foreign key(a) references tmp.a on update cascade')
        halftest.model.reconnect(reload=True)
        self.hotAssertOnUpdateCascade(self.RelB, CONST)

    def test_set_null(self):
        halftest.model.execute_query(DROP_CONST)
        halftest.model.execute_query('alter table tmp.b add constraint b_a_fkey foreign key(a) references tmp.a on update set null')
        halftest.model.reconnect(reload=True)
        self.hotAssertOnUpdateSetNull(self.RelB, CONST)

    def test_set_default(self):
        halftest.model.execute_query(DROP_CONST)
        halftest.model.execute_query('alter table tmp.b add constraint b_a_fkey foreign key(a) references tmp.a on update set default')
        halftest.model.reconnect(reload=True)
        self.hotAssertOnUpdateSetDefault(self.RelB, CONST)
