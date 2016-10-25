#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""This module provides the Model class.

The Model class allows to load the model of a database:
- model = Model(config_file='<config file name>')
 - model.desc() displays information on the structure of
   the database.
 - model.relation(<QRN>)
   see relation module for available methods on

About QRN and FQRN:
- FQRN stands for: Fully Qualified Relation Name. It is composed of:
  <database name>.<schema name>.<table name>.
  Only the schema name can have dots in it. In this case, you must double
  quote the schema name :
  <database connection filename>."<schema name>".<table name>
  ex:
  - one.public.my_table
  - two."access.role".acces
- QRN is the Qualified Relation Name. Same as the FQRN without the database
  name. Double quotes can be ommited even if there are dots in the schema name.

"""

__all__ = ["Model"]

import sys
import psycopg2
from psycopg2.extras import RealDictCursor

from configparser import ConfigParser
from collections import OrderedDict
from halfORM import model_errors
from halfORM.relation import _normalize_fqrn, _normalize_qrn, RelationFactory

psycopg2.extras.register_uuid()
#from pprint import PrettyPrinter

class Model(object):
    """Model class

    The model establishes a connection to the database and allows to
    generate a Relation object using model.relation(QRN) method.
    """
    __deja_vu = {}
    __metadata = {}
    def __init__(self, config_file=None, dbname=None, raise_error=True):
        """Model constructor

        Use @config_file in your scripts. The @dbname parameter is
        reserved to the RelationFactory metaclass.
        """
        assert bool(config_file) != bool(dbname)
        self.__config_file = config_file
        if dbname:
            self = self.__deja_vu[dbname]
            self.__dbname = dbname
            return
        self.__conn = None
        self.__cursor = None
        self.__relations = []
        try:
            self.connect()
        except Exception as err:
            if raise_error:
                raise err.__class__(err.filename)
            sys.stderr.write("{}\n".format(err))
            sys.stderr.flush()

    @staticmethod
    def deja_vu(dbname):
        """Returns None if the database hasn't been loaded yet.
        Otherwise, it returns the Model object already loaded.
        The Model object is shared between all the relations in the
        database. The Model object is loaded only once for a given database.
        """
        return Model.__deja_vu.get(dbname)

    def ping(self):
        """Returns True if the connection is OK.
        Otherwise attempt a new connection and return False.
        """
        try:
            self.execute_query("select 1");
            return True
        except:
            try:
                self.connect()
            except Exception as err:
                sys.stderr.write('{}\n'.format(err))
                sys.stderr.flush()
            return False

    def connect(self, **params):
        """Setup a new connexion, cursor to the database."""
        if self.__conn is not None:
            if not self.__conn.closed:
                self.__conn.close()
        config = ConfigParser()
        if not config.read(
                [self.__config_file,
                 '/etc/halfORM/{}'.format(self.__config_file)]):
            raise model_errors.MissingConfigFile(self.__config_file)
        params = dict(config['database'].items())
        needed_params = {'name', 'host', 'user', 'password', 'port'}
        self.__dbname = params['name']
        missing_params = needed_params.symmetric_difference(set(params.keys()))
        if missing_params:
            raise model_errors.MalformedConfigFile(
                self.__config_file, missing_params)
        self.__conn = psycopg2.connect(
            'dbname={name} host={host} user={user} '
            'password={password} port={port}'.format(**params),
            cursor_factory=RealDictCursor)
        self.__conn.autocommit = True
        self.__cursor = self.__conn.cursor()
        self.__metadata[self.__dbname] = self.__get_metadata()
        self.__deja_vu[self.__dbname] = self

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
                if table_key not in byname:
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
                if (tablekind, table_key) not in self.__relations:
                    self.__relations.append((tablekind, table_key))
        #pp = PrettyPrinter()
        #pp.pprint(metadata)
        self.__relations.sort()
        return metadata

    def execute_query(self, query, values=()):
        """Execute a raw SQL query"""
        return self.__cursor.execute(query, values)

    def relations(self):
        """List all the relations in the database"""
        for relation in self.__relations:
            yield "{} {}.{}.{}".format(relation[0], *relation[1])

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
            fqrn = '"{}".{}'.format(self.__dbname, _normalize_qrn(qrn=qrn))
            print(relation(fqrn))
