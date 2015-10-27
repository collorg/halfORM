#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""This module provides Model, RelationFactory and table

The Model class allows to load the model of a database:
- model = Model(config_file='<config file name>')
 - model.desc() displays information on the structure of
   the database.
 - model.relation(<QRN>)
   see relation_interface module for available methods on

The table function allows you to directly instanciate a Relation object
- table(<FQRN>)

The RelationFactory can be used to create classes to manipulate the relations
of the database:
```
class MyClass(metaclass=RelationFactory):
    fqrn = '<FQRN>'
```

About QRN and FQRN:
- FQRN stands for: Fully Qualified Relation Name. It is composed of:
  <database name>.<schema name>.<table name>.
  Only the schema name can have dots in it. In this case, it must be written
  <database name>."<schema name>".<table name>
- QRN is the Qualified Relation Name. Same as the FQRN without the database
  name. Double quotes can be ommited even if there are dots in the schema name.

"""

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
import psycopg2
from psycopg2.extras import RealDictCursor
from configparser import ConfigParser
from collections import OrderedDict
from halfORM import model_errors
#from pprint import PrettyPrinter

class Model():
    """Model class

    The model establishes a connection to the database and allows to
    generate a Relation object using model.relation(QRN) method.
    """
    __deja_vu = {}
    __metadata = {}
    def __init__(self, config_file=None, dbname=None):
        """Model constructor

        Use @config_file in your scripts. The @dbname parameter is
        reserved to the RelationFactory metaclass.
        """
        assert bool(config_file) != bool(dbname)
        if dbname:
            self = self.__deja_vu[dbname]
            self.__dbname = dbname
            return
        config = ConfigParser()
        if not config.read(config_file):
            raise model_errors.MissingConfigFile(config_file)
        params = dict(config['database'].items())
        needed_params = {'name', 'host', 'user', 'password', 'port'}
        self.__dbname = params['name']
        missing_params = needed_params.symmetric_difference(set(params.keys()))
        if missing_params:
            raise model_errors.MalformedConfigFile(config_file, missing_params)
        self.__conn = self.__connect(**params)
        self.__conn.autocommit = True
        self.__cursor = self.__conn.cursor()
        self.__metadata[self.__dbname] = self.__get_metadata()
        self.__deja_vu[self.__dbname] = self

    @staticmethod
    def deja_vu(dbname):
        """Returns None if the database hasn't been loaded yet.
        Otherwise, it returns the Model object already loaded.
        The Model object is shared between all the relations in the
        database. The Model object is loaded only once for a given database.
        """
        return Model.__deja_vu.get(dbname)

    def __connect(self, **params):
        """Returns the pyscopg2 connection object."""
        return psycopg2.connect(
            'dbname={name} host={host} user={user} '
            'password={password} port={port}'.format(**params),
            cursor_factory=RealDictCursor)

    @property
    def dbname(self):
        """
        property. Returns the database name.
        """
        return self.__dbname

    @property
    def connection(self):
        """
        Property. Returns the psycopg2 connection attached to the Model object.
        """
        return self.__conn

    @property
    def metadata(self):
        """Returns the metadata of the database.
        Uses the Model.__metadata class dictionary.
        """
        return self.__metadata[self.__dbname]

    def __get_metadata(self):
        """Loads the metadata by querying the request in the pg_metaview
        module.
        """
        from .pg_metaview import REQUEST
        metadata = {}
        byname = metadata['byname'] = OrderedDict()
        byid = metadata['byid'] = {}
        with self.connection.cursor() as cur:
            cur.execute(REQUEST)
            for dct in cur.fetchall():
                table_key = (
                    self.__dbname,
                    dct.pop('schemaname'), dct.pop('relationname'))
                tableid = dct.pop('tableid')
                if not table_key in byname:
                    byid[tableid] = {}
                    byid[tableid]['sfqrn'] = table_key
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
        """Instanciate an object of Relation, using the RelationFactory class.

        @qtn is the <schema>.<table> name of the relation
        @kwargs is a dictionary {field_name:value}
        """
        schema, table = qtn.rsplit('.', 1)
        fqrn = '.'.join([self.__dbname, '"{}"'.format(schema), table])
        fqrn, _ = _normalize_fqrn(fqrn)
        return RelationFactory(
            'Table', (), {'fqrn': fqrn, 'model': self})(**kwargs)

    def desc(self, qrn=None):
        """Prints the description of the relations of the model

        If an qualified relation name (<schema name>.<table name>) is
        passed, prints only the description of the corresponding relation.
        """
        if not qrn:
            for key in self.__metadata[self.__dbname]['byname']:
                fqrn = ".".join(['"{}"'.format(elt) for elt in key])
                print(relation(fqrn).desc())
        else:
            fqrn = '"{}".{}'.format(self.__dbname, _normalize_qrn(qrn))
            print(relation(fqrn).desc())

class FieldFactory(type):
    """FieldFactory metaclass
    """
    def __new__(mcs, clsname, bases, dct):
        from .field_interface import interface as field_interface
        ff_ = FieldFactory
        for fct_name, fct in field_interface.items():
            dct[fct_name] = fct
        return super(ff_, mcs).__new__(mcs, clsname, bases, dct)

class Field(metaclass=FieldFactory):
    pass

class RelationFactory(type):
    """RelationFactory Metaclass
    """
    re_split_fqrn = re.compile(r'\"\.\"|\"\.|\.\"|^\"|\"$')
    def __new__(mcs, class_name, bases, dct):
        def _gen_class_name(rel_kind, sfqrn):
            """Generates class name from relation kind and FQRN tuple"""
            class_name = "".join([elt.capitalize() for elt in
                                  [elt.replace('.', '') for elt in sfqrn]])
            return "{}_{}".format(rel_kind, class_name)

        from .relation_interface import (
            table_interface, view_interface, Relation)
        #TODO get bases from table inheritance
        bases = (Relation,)
        rf_ = RelationFactory
        tbl_attr = {}
        tbl_attr['__fqrn'], sfqrn = _normalize_fqrn(dct['fqrn'])
        if dct.get('model'):
            model = dct['model']
            tbl_attr['model'] = model
        tbl_attr['__sfqrn'] = tuple(sfqrn)
        attr_names = ['dbname', 'schemaname', 'relationname']
        for i in range(len(attr_names)):
            tbl_attr[attr_names[i]] = sfqrn[i]
        dbname = tbl_attr['dbname']
        tbl_attr['model'] = Model.deja_vu(dbname)
        if not tbl_attr['model']:
            tbl_attr['model'] = Model(dbname)
        rel_class_names = {'r': 'Table', 'v': 'View'}
        try:
            kind = (
                tbl_attr['model'].metadata['byname']
                [tuple(sfqrn)]['tablekind'])
            tbl_attr['__kind'] = rel_class_names[kind]
        except KeyError:
            raise model_errors.UnknownRelation(sfqrn)
        rel_interfaces = {'r': table_interface, 'v': view_interface}
        rf_.__set_fields(tbl_attr)
        for fct_name, fct in rel_interfaces[kind].items():
            tbl_attr[fct_name] = fct
        class_name = _gen_class_name(rel_class_names[kind], sfqrn)
        return super(rf_, mcs).__new__(mcs, class_name, (bases), tbl_attr)

    @staticmethod
    def __set_fields(ta_):
        """ta_: table attributes dictionary."""
        from .fkey import FKey
        ta_['__fields'] = []
        ta_['__fkeys'] = []
        dbm = ta_['model'].metadata
        for field_name, metadata in dbm['byname'][
                ta_['__sfqrn']]['fields'].items():
            fkeyname = metadata.get('fkeyname')
            if fkeyname and not fkeyname in ta_:
                ft_ = dbm['byid'][metadata['fkeytableid']]
                ft_sfqrn = ft_['sfqrn']
                fields_names = [ft_['fields'][elt]
                                for elt in metadata['fkeynum']]
                ft_fields_names = [ft_['fields'][elt]
                                   for elt in metadata['fkeynum']]
                ta_[fkeyname] = FKey(
                    fkeyname, ft_sfqrn, ft_fields_names, fields_names)
                ta_['__fkeys'].append(ta_[fkeyname])
            ta_[field_name] = Field(field_name, metadata)
            ta_['__fields'].append(ta_[field_name])

def _normalize_fqrn(fqrn):
    """
    fqrn can have the following forms:
    - 'a.b.c'
    - '"a"."b"."c"'
    - '"a"."b1.b2"."c"'
    - 'a."b1.b2".c'
    """
    rf_ = RelationFactory
    if fqrn.find('"') == -1:
        sfqrn = fqrn.split('.')
    else:
        sfqrn = [elt for elt in rf_.re_split_fqrn.split(fqrn) if elt]
    return '.'.join(['"{}"'.format(elt) for elt in sfqrn]), sfqrn

def _normalize_qrn(qrn):
    """
    qrn is the qualified relation name (<schema name>.<talbe name>)
    A schema name can have any number of dots in it.
    A table name can't have a dot in it.
    returns "<schema name>"."<relation name>"
    """
    return '.'.join(['"{}"'.format(elt) for elt in qrn.rsplit('.', 1)])

def relation(fqrn, **kwargs):
    """This function is used to instanciate a Relation object using
    its FQRN (Fully qualified relation name):
    <database name>.<schema name>.<relation name>.
    If the <schema name> comprises a dot it must be enclosed in double
    quotes. Dots are not allowed in <database name> and <relation name>.
    """
    return RelationFactory(None, None, {'fqrn': fqrn})(**kwargs)

