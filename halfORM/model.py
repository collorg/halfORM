#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""This module provides Model, RelationFactory and table

The Model class allows to load the model of a database:
- model = Model(config_file='<config file name>')
 - model.desc() displays information on the structure of
   the database.
 - model.relation(<QRN>)
   see relation module for available methods on

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

__all__ = ["Model"]

import psycopg2
from psycopg2.extras import RealDictCursor
from configparser import ConfigParser
from collections import OrderedDict
from halfORM import model_errors
from halfORM.relation import _normalize_fqrn, _normalize_qrn, RelationFactory
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
        if not config.read([config_file, '/etc/halfORM/{}'.format(config_file)]):
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
                description = dct.pop('tabledescription')
                if not table_key in byname:
                    byid[tableid] = {}
                    byid[tableid]['sfqrn'] = table_key
                    byid[tableid]['fields'] = {}
                    byname[table_key] = OrderedDict()
                    byname[table_key]['description'] = description
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
        from halfORM.relation import relation
        if not qrn:
            for key in self.__metadata[self.__dbname]['byname']:
                fqrn = ".".join(['"{}"'.format(elt) for elt in key])
                print(relation(fqrn))
        else:
            fqrn = '"{}".{}'.format(self.__dbname, _normalize_qrn(qrn))
            print(relation(fqrn))

