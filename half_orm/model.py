#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""This module provides the Model class.

The Model class allows to load the model of a database:
- model = Model(config_file='<config file name>')
 - model.desc() displays information on the structure of
   the database.
 - model.get_relation_class(<QRN>)
   see relation module for available methods on Relation class.

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

import os
import sys
from configparser import ConfigParser
from os import environ
import psycopg2
from psycopg2.extras import RealDictCursor

from half_orm import model_errors
from half_orm.relation import _normalize_fqrn, _normalize_qrn, _factory
from half_orm.pg_meta import PgMeta

CONF_DIR = os.path.abspath(environ.get('HALFORM_CONF_DIR', '/etc/half_orm'))

__all__ = ["Model", "camel_case"]

def camel_case(name):
    """Transform a string in camel case."""
    ccname = []
    name = name.lower()
    capitalize = True
    for char in name:
        if not char.isalnum():
            capitalize = True
            continue
        if capitalize:
            ccname.append(char.upper())
            capitalize = False
            continue
        ccname.append(char)
    return ''.join(ccname)

psycopg2.extras.register_uuid()

class Model:
    """Model class

    The model establishes a connection to the database and allows to
    generate a Relation object using model.relation(QRN) method.
    """
    __deja_vu = {}
    __metadata = {}
    _relations_ = {'classes': {}}
    def __init__(self,
                 config_file, dbname=None, scope=None, raise_error=True):
        """Model constructor

        Use @config_file in your scripts. The @dbname parameter is
        reserved to the _factory metaclass.
        """
        self.__backend_pid = None
        if bool(config_file) == bool(dbname):
            raise RuntimeError("You can't specify config_file with bdname!")
        self.__config_file = config_file
        self.__dbinfo = {}
        self.__dbname = dbname
        if Model._deja_vu(dbname):
            self.__dict__.update(Model._deja_vu(dbname))
            return
        self.__conn = None
        self._scope = scope and scope.split('.')[0]
        self.__raise_error = raise_error
        self.__production = False
        self._connect(raise_error=self.__raise_error)

    @staticmethod
    def _deja_vu(dbname):
        """Returns None if the database hasn't been loaded yet.
        Otherwise, it returns the Model object already loaded.
        The Model object is shared between all_ the relations in the
        database. The Model object is loaded only once for a given database.
        """
        return Model.__deja_vu.get(dbname)

    def ping(self):
        """Returns True if the connection is OK.

        Otherwise attempts a new connection and return False.
        """
        try:
            self.execute_query("select 1")
            return True
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            try:
                self._connect(raise_error=self.__raise_error)
            except psycopg2.OperationalError as err:
                sys.stderr.write(f'{err}\n')
                sys.stderr.flush()
            return False

    @property
    def production(self):
        """Returns the production status of the db. Production is set by adding
        production = True to the connexion file.

        Returns:
            bool: True if the database is in production, False otherwise
        """
        return self.__production

    def disconnect(self):
        """Disconnect
        """
        if self.__conn is not None:
            if not self.__conn.closed:
                self.__conn.close()

    def _connect(self, config_file=None, raise_error=True):
        """Setup a new connection to the database.

        If a config_file is provided, the connection is made with the new
        parameters, allowing to change role. The database name must be the same.

        The reconnect method is an alias to the connect method.
        """
        self.disconnect()
        if config_file:
            self.__config_file = config_file

        config = ConfigParser()

        if not config.read(
                [os.path.join(CONF_DIR, self.__config_file)]):
            raise model_errors.MissingConfigFile(os.path.join(CONF_DIR, self.__config_file))

        params = dict(config['database'].items())
        if config_file and params['name'] != self.__dbname:
            raise RuntimeError(
                f"Can't reconnect to another database {params['name']} != {self.__dbname}")
        self.__dbname = params['name']
        self.__dbinfo['name'] = params['name']
        self.__dbinfo['user'] = params.get('user')
        self.__dbinfo['password'] = params.get('password')
        self.__dbinfo['host'] = params.get('host')
        self.__dbinfo['port'] = params.get('port')
        self.__production = params.get('production', False)
        if self.__production == 'True':
            self.__production = True
        if self.__production == 'False':
            self.__production = False
        if not isinstance(self.__production, bool):
            raise ValueError
        if 'name' not in self.__dbinfo:
            raise model_errors.MalformedConfigFile(
                self.__config_file, {'name'})
        try:
            params = dict(self.__dbinfo)
            params['dbname'] = params.pop('name')
            self.__conn = psycopg2.connect(
                **params, cursor_factory=RealDictCursor)
        except psycopg2.OperationalError as err:
            if raise_error:
                raise err.__class__(err)
            sys.stderr.write(f"{err}\n")
            sys.stderr.flush()
        self.__conn.autocommit = True
        self.__pg_meta = PgMeta(self.__conn)
        self.__metadata = self.__pg_meta.metadata(self.__dbname)
        self.__deja_vu[self.__dbname] = self
        self.__backend_pid = self.execute_query(
            "select pg_backend_pid()").fetchone()['pg_backend_pid']

    reconnect = _connect

    @property
    def _pg_backend_pid(self):
        "backend PID"
        return self.__backend_pid

    @property
    def _dbname(self):
        """
        property. Returns the database name.
        """
        return self.__dbname

    @property
    def _connection(self):
        """\
        Property. Returns the psycopg2 connection attached to the Model object.
        """
        return self.__conn

    def fields_metadata(self, sfqrn):
        return self.__pg_meta.fields(self.__dbname, sfqrn)

    def fkeys_metadata(self, sfqrn):
        return self.__pg_meta.fkeys(self.__dbname, sfqrn)

    def relation_metadata(self, fqrn):
        return self.__pg_meta.relation(self.__dbname, fqrn)

    def execute_query(self, query, values=()):
        """Execute a raw SQL query"""
        cursor = self.__conn.cursor()
        cursor.execute(query, values)
        return cursor

    def get_relation_class(self, qtn):
        """Returns the class corresponding to the fqrn relation in the database.

        @qtn is the <schema>.<table> name of the relation
        @kwargs is a dictionary {field_name:value}
        """
        schema, table = qtn.rsplit('.', 1)
        fqrn = f'{self.__dbname}:"{schema}".{table}'
        fqrn, _ = _normalize_fqrn(fqrn)
        return _factory('Table', (), {'fqrn': fqrn, 'model': self})

    def has_relation(self, qtn):
        """Checks if the qtn is a relation in the database

        @qtn is in the form "<schema>".<table>
        Returns True if the relation exists, False otherwise.
        Also works for views and materialized views.
        """
        return self.__pg_meta.has_relation(self.__dbname, qtn)

    def _import_class(self, qtn, scope=None):
        """Used to return the class from the scope module.
        """
        stripped_qtn = qtn.replace('"', '')
        module_path = f'{scope or self._scope}.{stripped_qtn}'
        class_name = camel_case(qtn.split('.')[-1])
        module = __import__(
            module_path, globals(), locals(), [class_name], 0)
        if scope:
            self._scope = scope
        return module.__dict__[class_name]

    def _relations(self):
        """List all_ the relations in the database"""
        for relation in self.__pg_meta.relations_list:
            yield f"{relation[0]} {'.'.join(relation[1])}"

    def desc(self, qrn=None, type_=None):
        """Returns the list of the relations of the model.

        Each line contains:
        - the relation type: 'r' relation, 'v' view, 'm' materialized view,
        - the quoted FQRN (Fully qualified relation name)
          <"db name">:"<schema name>"."<relation name>"
        - the list of the FQRN of the inherited relations.

        If a qualified relation name (<schema name>.<table name>) is
        passed, prints only the description of the corresponding relation.
        """
        return self.__pg_meta.desc(self.__dbname, qrn, type_)

    def __str__(self):
        return self.__pg_meta.str(self.__dbname)