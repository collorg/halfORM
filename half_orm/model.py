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
from half_orm.relation import _factory
from half_orm import pg_meta


CONF_DIR = os.path.abspath(environ.get('HALFORM_CONF_DIR', '/etc/half_orm'))


psycopg2.extras.register_uuid()

class Model:
    """Model class

    The model establishes a connection to the database and allows to
    generate a Relation object using model.relation(QRN) method.
    """
    __deja_vu = {}
    _classes_ = {}
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
        if (dbname):
            Model._classes_[dbname] = {}
        self.__conn = None
        self._scope = scope and scope.split('.')[0]
        self.__raise_error = raise_error
        self.__production = False
        self.__connect(raise_error=self.__raise_error)

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
                self.__connect(raise_error=self.__raise_error)
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

    def __connect(self, config_file=None, raise_error=True, reload=False):
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
        self.__pg_meta = pg_meta.PgMeta(self.__conn, reload)
        self.__deja_vu[self.__dbname] = self
        self.__backend_pid = self.execute_query(
            "select pg_backend_pid()").fetchone()['pg_backend_pid']

    reconnect = __connect

    def reload(self, config_file=None, raise_error=True):
        "Reload metadata"
        self.__connect(config_file, raise_error, True)

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
        "Proxy to PgMeta.fields_meta"
        return self.__pg_meta.fields_meta(self.__dbname, sfqrn)

    def fkeys_metadata(self, sfqrn):
        "Proxy to PgMeta.fkeys_meta"
        return self.__pg_meta.fkeys_meta(self.__dbname, sfqrn)

    def relation_metadata(self, fqrn):
        "Proxy to PgMeta.relation_meta"
        return self.__pg_meta.relation_meta(self.__dbname, fqrn)

    def unique_constraints_list(self, fqrn):
        "Proxy to PgMeta.unique_constraints_list"
        return self.__pg_meta.unique_constraints_list(self.__dbname, fqrn)

    def pkey_constraint(self, fqrn):
        "Proxy to PgMeta.pkey_constraint"
        return self.__pg_meta.pkey_constraint(self.__dbname, fqrn)

    def execute_query(self, query, values=()):
        """Execute a raw SQL query"""
        cursor = self.__conn.cursor()
        cursor.execute(query, values)
        return cursor

    def execute_function(self, fct_name, *args, **kwargs):
        """Execute a PostgreSQL function with named parameters.

        returns a list of tuples
        """
        if bool(args) and bool(kwargs):
            raise RuntimeError("You can't mix args and kwargs with the execute_function method!")
        cursor = self.__conn.cursor()
        if kwargs:
            values = kwargs
        else:
            values = args
        cursor.callproc(fct_name, values)
        return cursor.fetchall()

    def call_procedure(self, proc_name, *args, **kwargs):
        "Execute a PostgreSQL procedure"
        if bool(args) and bool(kwargs):
            raise RuntimeError("You can't mix args and kwargs with the call_procedure method!")
        if kwargs:
            params = ', '.join([f'{key} => %s' for key in kwargs])
            values = tuple(kwargs.values())
        else:
            params = ', '.join(['%s' for elt in range(len(args))])
            values = args
        query = f'call {proc_name}({params})'
        cursor = self.__conn.cursor()
        cursor.execute(query, values)
        try:
            return cursor.fetchall()
        except psycopg2.ProgrammingError:
            return None

    def get_relation_class(self, qtn):
        """Returns the class corresponding to the fqrn relation in the database.

        @qtn is the <schema>.<table> name of the relation
        @kwargs is a dictionary {field_name:value}
        """
        schema, table = qtn.replace('"', '').rsplit('.', 1)
        return _factory({'fqrn': (self.__dbname, schema, table), 'model': self})

    def has_relation(self, qtn):
        """Checks if the qtn is a relation in the database

        @qtn is in the form "<schema>".<table>
        Returns True if the relation exists, False otherwise.
        Also works for views and materialized views.
        """
        return self.__pg_meta.has_relation(self.__dbname, *qtn.rsplit('.', 1))

    @classmethod
    def check_deja_vu_class(cls, dbname, schema, relation):
        """Not to use with _import_class.
        """
        if cls._classes_.get(dbname):
            return cls._classes_[dbname].get((dbname, schema, relation))

    def _import_class(self, qtn, scope=None):
        """Used to return the class from the scope module.

        This method is used to import a class from a module. The module
        must reside in an accessible python package named `scope`.
        """
        t_qtn = qtn.replace('"', '').rsplit('.', 1)
        module_path = f'{scope or self._scope}.{".".join(t_qtn)}'
        _class_name = pg_meta.class_name(qtn) # XXX
        module = __import__(
            module_path, globals(), locals(), [_class_name], 0)
        if scope:
            self._scope = scope
        return module.__dict__[_class_name]

    def _relations(self):
        """List all_ the relations in the database"""
        rels = self.__pg_meta.relations_list(self.__dbname)
        return rels

    def desc(self):
        """Returns the list of the relations of the model.

        Each line contains:
        - the relation type: 'r' relation, 'v' view, 'm' materialized view,
        - the quoted FQRN (Fully qualified relation name)
          <"db name">:"<schema name>"."<relation name>"
        - the list of the FQRN of the inherited relations.
        """
        return self.__pg_meta.desc(self.__dbname)

    def __str__(self):
        return self.__pg_meta.str(self.__dbname)