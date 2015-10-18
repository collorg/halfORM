#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import re
import sys
import psycopg2, psycopg2.extras

def init_table(self, **kwargs):
    self.bla = 'blabla'

def repr_table(self):
    return ('dbname: {dbname}, schemaname: {schemaname},'
            ' tablename: {tablename}').format(**vars(self.__class__))

class TableFactory(type):
    __deja_vu = {}
    re_split_fqtn = re.compile('\"\.\"|\"\.|\.\"|^\"|\"$')
    def __new__(cls, clsname, bases, dct):
        TF = TableFactory
        tbl_attr = {}
        TF.__split_fqtn(dct['fqtn'], tbl_attr)
        tbl_attr['__init__'] = init_table
        tbl_attr['__repr__'] = repr_table
        return super(TF, cls).__new__(cls, clsname, bases, tbl_attr)

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
    def todo():
        con = psycopg2.connect('dbname={} host=localhost'.format(dbname))
        cur = con.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("select column_name from information_schema.columns "
                    " where "
                    "table_catalog=%s and "
                    "table_schema=%s and "
                    "table_name=%s",
                    (dbname, schemaname, tablename))
        return cls

class OidTable(metaclass=TableFactory):
    fqtn = 'dpt_info."collorg.core".oid_table'

if __name__ == '__main__':
    oidt = OidTable()
    print(type(oidt))
    print(oidt)
    sys.exit()
    print(table('a."b"."c"'))
    print(Table('"a"."b"."c"'))
    print(Table('"a"."b1.b2".c'))
    print(Table('a."b1.b2".c'))
    print(Table('"a.b"."b1.b2".c'))
