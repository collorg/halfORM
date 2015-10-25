#!/usr/bin/env python3
#-*- coding: utf-8 -*-

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

__all__ = ["Model", "relation"]

import re
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from configparser import ConfigParser
from collections import OrderedDict
from halfORM import model_errors
from pprint import PrettyPrinter

class Model():
    def __init__(self, dbname, config_file_path='/etc/halfORM/'):
        self.__dbname = dbname
        self.__config_file_path = config_file_path
        self.__conn = self.__connect()
        self.__cursor = self.__conn.cursor()
        self.__metadata = self.get()

    def __connect(self):
        config_file_name = (
            '{}/{}'.format(self.__config_file_path, self.__dbname))
        config = ConfigParser()
        ok = config.read(config_file_name)
        if not ok:
            raise model_errors.MissingConfigFile(config_file_name)
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
        metadata = {}
        byname = metadata['byname'] = OrderedDict()
        byid = metadata['byid'] = {}
        with self.new_cursor() as cur:
            cur.execute(request)
            for dct in cur.fetchall():
                table_key = (
                    self.__dbname, dct.pop('schemaname'), dct.pop('tablename'))
                tableid = dct.pop('tableid')
                if not table_key in byname:
                    byid[tableid] = {}
                    byid[tableid]['sfqtn'] = table_key
                    byid[tableid]['fields'] = {}
                    byname[table_key] = OrderedDict()
                    byname[table_key]['fields'] = OrderedDict()
                    byname[table_key]['fields_by_num'] = OrderedDict()
                fieldname = dct.pop('fieldname')
                fieldnum = dct['fieldnum']
                tablekind = dct.pop('tablekind')
                byname[table_key]['tablekind'] = tablekind
                byname[table_key]['fields'][fieldname] = dct
                byname[table_key]['fields_by_num'][fieldnum] = dct
                byid[tableid]['fields'][fieldnum] = fieldname
        #pp = PrettyPrinter()
        #pp.pprint(metadata)
        return metadata

    def relation(self, qtn, **kwargs):
        """qtn is the <schema>.<table> name of the relation"""
        schema, table = qtn.rsplit('.', 1)
        fqtn = '.'.join([self.__dbname, '"{}"'.format(schema), table])
        fqtn, _ = _normalize_fqtn(fqtn)
        return RelationFactory(
            'Table', (), {'fqtn': fqtn, 'model': self})(**kwargs)

    def desc(self):
        for key in self.__metadata['byname']:
            print(relation(".".join(['"{}"'.format(elt) for elt in key])))

class FieldFactory(type):
    def __new__(cls, clsname, bases, dct):
        from .field_interface import interface as field_interface
        FF = FieldFactory
        for fct_name, fct in field_interface.items():
            dct[fct_name] = fct
        return super(FF, cls).__new__(cls, clsname, bases, dct)

class Fkey():
    def __init__(self, fk_name, fk_sfqtn, fk_names, fields):
        self.__name = fk_name
        self.__fk_fqtn = ".".join(['"{}"'.format(elt) for elt in fk_sfqtn])
        self.__fk_names = fk_names
        self.__fields = fields

    def __repr__(self):
        fields = '({})'.format(', '.join(self.__fields))
        return "FK {}: {}\n \u21B3 {}({})".format(
            self.__name,
            fields, self.__fk_fqtn, ', '.join(self.__fk_names))

class Field(metaclass=FieldFactory):
    pass

class RelationFactory(type):
    __deja_vu = {}
    re_split_fqtn = re.compile(r'\"\.\"|\"\.|\.\"|^\"|\"$')
    def __new__(cls, classname, bases, dct):
        def _gen_class_name(rel_kind, sfqtn):
            class_name = "".join([elt.capitalize() for elt in
                                  [elt.replace('.', '') for elt in sfqtn]])
            return "{}_{}".format(rel_kind, class_name)

        from .relation_interface import (
            table_interface, view_interface, Relation)
        #TODO get bases from table inheritance
        bases = (Relation,)
        TF = RelationFactory
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
        try:
            tbl_attr['__kind'] = (
                tbl_attr['model'].metadata['byname'][tuple(sfqtn)]['tablekind'])
        except KeyError:
            raise model_errors.UnknownRelation(sfqtn)
        kind = tbl_attr['__kind']
        rel_interfaces = {'r': table_interface, 'v': view_interface}
        rel_class_names = {'r': 'Table', 'v': 'View'}
        TF.__set_fields(tbl_attr)
        for fct_name, fct in rel_interfaces[kind].items():
            tbl_attr[fct_name] = fct
        class_name = _gen_class_name(rel_class_names[kind], sfqtn)
        return super(TF, cls).__new__(cls, class_name, (bases), tbl_attr)

    @staticmethod
    def __set_fields(ta):
        """ta: table attributes dictionary."""
        ta['__fields'] = []
        ta['__fkeys'] = []
        dbm = ta['model'].metadata
        for field_name, metadata in dbm['byname'][
                ta['__sfqtn']]['fields'].items():
            fkeyname = metadata.get('fkeyname')
            if fkeyname and not fkeyname in ta:
                ft = dbm['byid'][metadata['fkeytableid']]
                ft_sfqtn = ft['sfqtn']
                fields_names = [ft['fields'][elt]
                                   for elt in metadata['fkeynum']]
                ft_fields_names = [ft['fields'][elt]
                                   for elt in metadata['fkeynum']]
                ta[fkeyname] = Fkey(
                    fkeyname, ft_sfqtn, ft_fields_names, fields_names)
                ta['__fkeys'].append(ta[fkeyname])
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
    TF = RelationFactory
    if fqtn.find('"') == -1:
        sfqtn = fqtn.split('.')
    else:
        sfqtn = [elt for elt in TF.re_split_fqtn.split(fqtn) if elt]
    return '.'.join(['"{}"'.format(elt) for elt in sfqtn]), sfqtn

def relation(fqtn, **kwargs):
    return RelationFactory(None, None, {'fqtn': fqtn})(**kwargs)

