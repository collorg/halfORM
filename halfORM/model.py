#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import re
import sys
import psycopg2
from .field_interface import interface as field_interface
from .table_interface import interface as table_interface
from psycopg2.extras import RealDictCursor
from configparser import ConfigParser
from collections import OrderedDict
from pprint import PrettyPrinter

# This method can't be moved in table_interface module
def __call__(self, **kwargs):
    """__call__ method for the class Table
    """
    return table(self.__fqtn, **kwargs)

table_interface.update({'__call__': __call__})

sql_db_struct = """
SELECT
    a.attrelid AS tableid,
    array_agg( i.inhseqno::TEXT || ':' || i.inhparent::TEXT ) AS inherits,
    c.relkind AS tablekind,
    n.nspname AS schemaname,
    c.relname AS tablename,
    tdesc.description AS tabledescription,
    a.attname AS fieldname,
    adesc.description AS fielddescription,
    a.attndims AS fielddim,
    pt.typname AS fieldtype,
    a.attnum AS fieldnum,
    NOT( a.attislocal ) AS inherited,
    cn_uniq.contype AS uniq,
    a.attnotnull OR NULL AS notnull,
    cn_pk.contype AS pkey,
    cn_fk.contype AS fkey,
    cn_fk.conname AS fkeyname,
    cn_fk.conkey AS keynum,
    cn_fk.confrelid AS fkeytableid,
    cn_fk.confkey AS fkeynum
FROM
    pg_class c -- table
    LEFT JOIN pg_description tdesc ON
    tdesc.objoid = c.oid AND
    tdesc.objsubid = 0
    LEFT JOIN pg_namespace n ON
    n.oid = c.relnamespace
    LEFT JOIN pg_inherits i ON
    i.inhrelid = c.oid
    LEFT JOIN pg_attribute a ON
    a.attrelid = c.oid
    LEFT JOIN pg_description adesc ON
    adesc.objoid = c.oid AND
    adesc.objsubid = a.attnum
    JOIN pg_type pt ON
    a.atttypid = pt.oid
    LEFT JOIN pg_constraint cn_uniq ON
    cn_uniq.contype = 'u' AND
    cn_uniq.conrelid = a.attrelid AND
    a.attnum = ANY( cn_uniq.conkey )
    LEFT JOIN pg_constraint cn_pk ON
    cn_pk.contype = 'p' AND
    cn_pk.conrelid = a.attrelid AND
    a.attnum = ANY( cn_pk.conkey )
    LEFT JOIN pg_constraint cn_fk ON
    cn_fk.contype = 'f' AND
    cn_fk.conrelid = a.attrelid AND
    a.attnum = ANY( cn_fk.conkey )
WHERE
    n.nspname <> 'pg_catalog'::name AND
    n.nspname <> 'information_schema'::name AND
    ( c.relkind = 'r'::"char" OR c.relkind = 'v'::"char" ) AND
    a.attnum > 0 -- AND
GROUP BY
    a.attrelid,
    n.nspname,
    c.relname,
    tdesc.description,
    c.relkind,
    a.attnum,
    a.attname,
    adesc.description,
    a.attndims,
    a.attislocal,
    pt.typname,
    cn_uniq.contype,
    a.attnotnull,
    cn_pk.contype,
    cn_fk.contype,
    cn_fk.conname,
    cn_fk.conkey,
    cn_fk.confrelid,
    cn_fk.confkey
ORDER BY
    n.nspname, c.relname, a.attnum
"""

class Model():
    def __init__(self, dbname):
        self.__name = dbname
        self.__conn = self.__connect()
        self.__metadata = self.get()

    def __connect(self):
        config = ConfigParser()
        config.read('/etc/halfORM/{}'.format(self.__name))
        params = dict(config['database'].items())
        params['dbname'] = self.__name
        return psycopg2.connect(
            'dbname={dbname} host={host} user={user} '
            'password={password} port={port}'.format(**params),
            cursor_factory=RealDictCursor)

    def cursor(self):
        return self.__conn.cursor()
    def commit(self):
        return self.__conn.commit()
    def rollback(self):
        return self.__conn.rollback()
    def close(self):
        return self.__conn.close()

    @property
    def metadata(self):
        return self.__metadata

    def get(self):
        metadata = OrderedDict()
        with self.cursor() as cur:
            cur.execute(sql_db_struct)
            for dct in cur.fetchall():
                table_key = (
                    self.__name, dct.pop('schemaname'), dct.pop('tablename'))
                if not table_key in metadata:
                    metadata[table_key] = OrderedDict()
                    metadata[table_key]['fields'] = OrderedDict()
                metadata[table_key]['tablekind'] = dct.pop('tablekind')
                metadata[table_key]['fields'][dct['fieldname']] = dct
        #pp = PrettyPrinter()
        #pp.pprint(metadata)
        return metadata

    def desc(self):
        for key in self.__metadata:
            print(table(".".join(['"{}"'.format(elt) for elt in key])))

class FieldFactory(type):
    def __new__(cls, clsname, bases, dct):
        FF = FieldFactory
        for fct_name, fct in field_interface.items():
            dct[fct_name] = fct
        return super(FF, cls).__new__(cls, clsname, bases, dct)

class Field(metaclass=FieldFactory):
    pass

class Table():
    pass

class TableFactory(type):
    __deja_vu = {}
    re_split_fqtn = re.compile(r'\"\.\"|\"\.|\.\"|^\"|\"$')
    def __new__(cls, clsname, bases, dct):
        TF = TableFactory
        tbl_attr = {}
        tbl_attr['__fqtn'], sfqtn = _normalize_fqtn(dct['fqtn'])
        tbl_attr['__sfqtn'] = tuple(sfqtn)
        attr_names = ['dbname', 'schemaname', 'tablename']
        for i in range(len(attr_names)):
            tbl_attr[attr_names[i]] = sfqtn[i]
        dbname = tbl_attr['dbname']
        if not dbname in TF.__deja_vu.keys():
            model = Model(dbname)
            tbl_attr['model'] = model
            TF.__deja_vu[dbname] = model
        else:
            tbl_attr['model'] = TF.__deja_vu[dbname]
        TF.__metadata = TF.__deja_vu[dbname]
        tbl_attr['__kind'] = (
            tbl_attr['model'].metadata[tuple(sfqtn)]['tablekind'])
        TF.__set_fields(tbl_attr)
        for fct_name, fct in table_interface.items():
            tbl_attr[fct_name] = fct
        return super(TF, cls).__new__(cls, 'Table', bases, tbl_attr)

    @staticmethod
    def __set_fields(ta):
        """ta: table attributes dictionary."""
        ta['__fields'] = []
        for field_name, metadata in ta['model'].metadata[
                ta['__sfqtn']]['fields'].items():
            ta[field_name] = Field(field_name, metadata)
            ta['__fields'].append(ta[field_name])

def _normalize_fqtn(fqtn):
    """
    fqtn can have the following forms:
    - 'a.b.c'
    - '"a"."b"."c"'
    - '"a"."b1.b2"."c"'
    - 'a."b1.b2".c'
    """
    TF = TableFactory
    if fqtn.find('"') == -1:
        sfqtn = fqtn.split('.')
    else:
        sfqtn = [elt for elt in TF.re_split_fqtn.split(fqtn) if elt]
    return '.'.join(['"{}"'.format(elt) for elt in sfqtn]), sfqtn

def table(fqtn, **kwargs):
    return TableFactory('Table', (), {'fqtn': fqtn})(**kwargs)

def gen_class_name(fqtn):
    fqtn, sfqtn = _normalize_fqtn(fqtn)
    class_name = "".join([elt.capitalize() for elt in
                          [elt.replace('.', '_') for elt in sfqtn]])
    return class_name
