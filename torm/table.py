#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import re
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from configparser import ConfigParser
from collections import OrderedDict

def init_field(self, name):
    self.__name = name

def repr_field(self):
    return self.__name

class FieldFactory(type):
    def __new__(cls, clsname, bases, dct):
        FF = FieldFactory
        dct['__init__'] = init_field
        dct['__repr__'] = repr_field
        return super(FF, cls).__new__(cls, clsname, bases, dct)

class Field(metaclass=FieldFactory):
    pass

def init_table(self, **kwargs):
    """Fields init with kwargs"""

def repr_table(self):
    ret = [('dbname: {dbname}, schemaname: {schemaname},'
           ' tablename: {tablename}').format(**vars(self.__class__))]
    for field in self.__fields:
        ret.append('- {}'.format(field))
    return '\n'.join(ret)

class TableFactory(type):
    __deja_vu = {}
    re_split_fqtn = re.compile(r'\"\.\"|\"\.|\.\"|^\"|\"$')
    def __new__(cls, clsname, bases, dct):
        TF = TableFactory
        tbl_attr = {}
        TF.__split_fqtn(dct['fqtn'], tbl_attr)
        tbl_attr['conn'] = TF.__connect(tbl_attr['dbname'])
        TF.__set_fields(tbl_attr)
        tbl_attr['__init__'] = init_table
        tbl_attr['__repr__'] = repr_table
        return super(TF, cls).__new__(cls, clsname, bases, tbl_attr)

    @staticmethod
    def __connect(dbname):
        config = ConfigParser()
        config.read('/etc/torm/{}'.format(dbname))
        params = dict(config['database'].items())
        params['dbname'] = dbname
        return psycopg2.connect('dbname={dbname} host={host} user={user} '
                                'password={password} port={port}'.format(**params),
                                cursor_factory=RealDictCursor)

    @staticmethod
    def __split_fqtn(fqtn, tbl_attr):
        """
        fqtn can have the following forms:
        - 'a.b.c'
        - '"a"."b"."c"'
        - '"a"."b1.b2"."c"'
        - 'a."b1.b2".c'
        """
        attr_names = ['dbname', 'schemaname', 'tablename']
        TF = TableFactory
        if fqtn.find('"') == -1:
            sfqtn = fqtn.split('.')
        else:
            sfqtn = [elt for elt in TF.re_split_fqtn.split(fqtn) if elt]
        for i in range(len(attr_names)):
            tbl_attr[attr_names[i]] = sfqtn[i]
        tbl_attr['fqtn'] = '.'.join(['"{}"'.format(elt) for elt in sfqtn])

    @staticmethod
    def __set_fields(tbl_attr):
        cur = tbl_attr['conn'].cursor()
        ta = tbl_attr
        cur.execute("select column_name from information_schema.columns"
                    " where "
                    " table_catalog=%s and table_schema=%s and table_name=%s",
                    (ta['dbname'], ta['schemaname'], ta['tablename']))
        tbl_attr['__fields'] = []
        for dct in cur.fetchall():
            field_name = "{}_".format(dct['column_name'])
            tbl_attr[field_name] = Field(field_name)
            tbl_attr['__fields'].append(tbl_attr[field_name])

class OidTable(metaclass=TableFactory):
    fqtn = 'dpt_info."collorg.core".oid_table'

class BaseTable(metaclass=TableFactory):
    fqtn = 'dpt_info."collorg.core".base_table'


class ViewSession(metaclass=TableFactory):
    fqtn = 'dpt_info."seminaire.view".session'

if __name__ == '__main__':
    oidt = OidTable()
    print(type(oidt))
    print(vars(oidt.__class__))
    print(oidt)
    bt = BaseTable()
    print(bt)
    vs = ViewSession()
    print(vs)
    sys.exit()
    print(table('a."b"."c"'))
    print(Table('"a"."b"."c"'))
    print(Table('"a"."b1.b2".c'))
    print(Table('a."b1.b2".c'))
    print(Table('"a.b"."b1.b2".c'))
