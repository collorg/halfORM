#!/usr/bin/env python3
#-*- coding: utf-8 -*-

__version__ = "0.0.1"
__author__ = "Joël Maïzi <joel.maizi@lirmm.fr>"
__copyright__ = "Copyright (c) 2015 Joël Maïzi"
__license__ = """
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import re
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from configparser import ConfigParser
from collections import OrderedDict
from pprint import PrettyPrinter

class Model():
    def __init__(self, dbname, config_file_path='/etc/halfORM/'):
        print('Model.__init__')
        self.__dbname = dbname
        self.__config_file_path = config_file_path
        self.__conn = self.__connect()
        self.__cursor = self.__conn.cursor()
        self.__metadata = self.get()

    def __connect(self):
        config = ConfigParser()
        config.read('{}/{}'.format(self.__config_file_path, self.__dbname))
        params = dict(config['database'].items())
        params['dbname'] = self.__dbname
        return psycopg2.connect(
            'dbname={dbname} host={host} user={user} '
            'password={password} port={port}'.format(**params),
            cursor_factory=RealDictCursor)

    @property
    def dbname(self):
        return self.__dbname

    @property
    def cursor(self):
        return self.__cursor

    def new_cursor(self):
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
        from .pg_metaview import request
        metadata = OrderedDict()
        with self.new_cursor() as cur:
            cur.execute(request)
            for dct in cur.fetchall():
                table_key = (
                    self.__dbname, dct.pop('schemaname'), dct.pop('tablename'))
                if not table_key in metadata:
                    metadata[table_key] = OrderedDict()
                    metadata[table_key]['fields'] = OrderedDict()
                metadata[table_key]['tablekind'] = dct.pop('tablekind')
                metadata[table_key]['fields'][dct['fieldname']] = dct
        #pp = PrettyPrinter()
        #pp.pprint(metadata)
        return metadata

    def relation(self, qtn, **kwargs):
        """qtn is the <schema>.<table> name of the relation"""
        schema, table = qtn.rsplit('.', 1)
        fqtn = '.'.join([self.__dbname, '"{}"'.format(schema), table])
        fqtn, _ = _normalize_fqtn(fqtn)
        return TableFactory(
            'Table', (), {'fqtn': fqtn, 'model': self})(**kwargs)

    def desc(self):
        for key in self.__metadata:
            print(table(".".join(['"{}"'.format(elt) for elt in key])))

class FieldFactory(type):
    def __new__(cls, clsname, bases, dct):
        from .field_interface import interface as field_interface
        FF = FieldFactory
        for fct_name, fct in field_interface.items():
            dct[fct_name] = fct
        return super(FF, cls).__new__(cls, clsname, bases, dct)

class Field(metaclass=FieldFactory):
    pass

class TableFactory(type):
    __deja_vu = {}
    re_split_fqtn = re.compile(r'\"\.\"|\"\.|\.\"|^\"|\"$')
    def __new__(cls, clsname, bases, dct):
        from .relation_interface import (
            table_interface, view_interface, Relation)
        bases = tuple(list(bases) + [Relation])
        TF = TableFactory
        tbl_attr = {}
        tbl_attr['__fqtn'], sfqtn = _normalize_fqtn(dct['fqtn'])
        if dct.get('model'):
            model = dct['model']
            tbl_attr['model'] = model
            TF.__deja_vu[model.dbname] = model
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
        kind = tbl_attr['__kind']
        rel_interfaces = {'r': table_interface, 'v': view_interface}
        rel_class_names = {'r': 'Table', 'v': 'View'}
        TF.__set_fields(tbl_attr)
        for fct_name, fct in rel_interfaces[kind].items():
            tbl_attr[fct_name] = fct
        return super(TF, cls).__new__(
            cls, rel_class_names[kind], (bases), tbl_attr)

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
