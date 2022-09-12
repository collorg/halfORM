#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""This module provides the class Model."""


import os
import sys
from configparser import ConfigParser
from os import environ
import psycopg2
from psycopg2.extras import RealDictCursor

from half_orm.model_errors import MalformedConfigFile, MissingConfigFile, MissingSchemaInName, UnknownRelation
from half_orm.relation import Relation, REL_INTERFACES, REL_CLASS_NAMES
from half_orm import pg_meta
from half_orm.pg_meta import normalize_fqrn, normalize_qrn

CONF_DIR = os.path.abspath(environ.get('HALFORM_CONF_DIR', '/etc/half_orm'))


psycopg2.extras.register_uuid()

class Model:
    """The class Model is responsible for the connection to the PostgreSQL database.
    
    Once connected, you can use the
    `get_relation_class <#half_orm.model.Model.get_relation_class>`_
    method to generate a class to access any relation (table/view) in your database.

    Example:
        >>> from half_orm.model import Model
        >>> model = Model('my_config_file')
        >>> class MyTable(model.get_relation_class('my_schema.my_table')):
        ...     # Your business code goes here


    """
    __deja_vu = {}
    _classes_ = {}
    def __init__(self, config_file, scope=None):
        """Model constructor

        Use @config_file in your scripts. The @dbname parameter is
        reserved to the __factory metaclass.
        """
        self.__backend_pid = None
        self.__config_file = config_file
        self.__dbinfo = {}
        self.__dbname = None
        self.__conn = None
        self._scope = scope and scope.split('.')[0]
        self.__production = False
        self.__connect()

    def get_relation_class(self, relation_name: str) -> 'class(Relation)':
        """This method is a factory that generates a class that inherits the `Relation <#half_orm.relation.Relation>`_ class.

        Args:
            relation_name (string): the full name (`<schema>.<relation>`) of the targeted relation in the database.

        Raises:
            ValueError: if the schema is missing in relation_name
            UnknownRelationError: if the relation is not found in the database

        Returns:
            a class that inherits the `Relation <#half_orm.relation.Relation>`_ class:
                the class corresponding to the relation in the database.

        Examples:
            A class inheriting the `Relation <#half_orm.relation.Relation>`_ class is returned:
                >>> Person = model.get_relation_class('actor.person')
                >>> Person
                <class 'half_orm.relation.Table_HalftestActorPerson'>
                >>> Person.__bases__
                (<class 'half_orm.relation.Relation'>,)

            A `MissingSchemaInName <#half_orm.model_errors.MissingSchemaInName>`_ is raised when the schema name is missing:
                >>> model.get_relation_class('person')
                [...]MissingSchemaInName: do you mean 'public.person'?

            An `UnknownRelation <#half_orm.model_errors.UnknownRelation>`_ is raised if the relation is not found in the model:
                >>> model.get_relation_class('public.person')
                [...]UnknownRelation: 'public.person' does not exist in the database halftest.
        """

        def factory(dct):
            """Function to build a Relation class corresponding to a PostgreSQL
            relation.
            """
            def _gen_class_name(rel_kind, sfqrn):
                """Generates class name from relation kind and FQRN tuple"""
                class_name = "".join([elt.capitalize() for elt in
                                    [elt.replace('.', '') for elt in sfqrn]])
                return f"{rel_kind}_{class_name}"

            bases = [Relation,]
            tbl_attr = {}
            tbl_attr['__base_classes'] = set()
            tbl_attr['__fkeys_properties'] = False
            tbl_attr['_qrn'] = normalize_qrn(dct['fqrn'])

            tbl_attr.update(dict(zip(['_dbname', '_schemaname', '_relationname'], dct['fqrn'])))
            if not tbl_attr['_dbname'] in Model._classes_:
                Model._classes_[tbl_attr['_dbname']] = {}
            if dct.get('model'):
                tbl_attr['_model'] = dct['model']
            else:
                tbl_attr['_model'] = Model._deja_vu(tbl_attr['_dbname'])
            rel_class = Model._check_deja_vu_class(*dct['fqrn'])
            if rel_class:
                return rel_class

            try:
                metadata = tbl_attr['_model']._relation_metadata(dct['fqrn'])
            except KeyError as exc:
                raise UnknownRelation(dct['fqrn']) from exc
            if metadata['inherits']:
                metadata['inherits'].sort()
                bases = []
            for parent_fqrn in metadata['inherits']:
                bases.append(factory({'fqrn': parent_fqrn}))
            tbl_attr['__metadata'] = metadata
            tbl_attr['_t_fqrn'] = dct['fqrn']
            tbl_attr['_fqrn'] = normalize_fqrn(dct['fqrn'])
            tbl_attr['__kind'] = REL_CLASS_NAMES[metadata['tablekind']]
            tbl_attr['_fkeys'] = []
            for fct_name, fct in REL_INTERFACES[metadata['tablekind']].items():
                tbl_attr[fct_name] = fct
            class_name = _gen_class_name(REL_CLASS_NAMES[metadata['tablekind']], dct['fqrn'])
            rel_class = type(class_name, tuple(bases), tbl_attr)
            Model._classes_[tbl_attr['_dbname']][dct['fqrn']] = rel_class
            return rel_class

        try:
            schema, table = relation_name.replace('"', '').rsplit('.', 1)
        except ValueError as err:
            raise MissingSchemaInName(relation_name) from err
        return factory({'fqrn': (self.__dbname, schema, table), 'model': self})


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
                self.__connect()
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

    def __connect(self, config_file=None, reload=False):
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
            raise MissingConfigFile(os.path.join(CONF_DIR, self.__config_file))

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
            raise MalformedConfigFile(
                self.__config_file, {'name'})
        try:
            params = dict(self.__dbinfo)
            params['dbname'] = params.pop('name')
            self.__conn = psycopg2.connect(
                **params, cursor_factory=RealDictCursor)
        except psycopg2.OperationalError as err:
            raise err.__class__(err)
        self.__conn.autocommit = True
        self.__pg_meta = pg_meta.PgMeta(self.__conn, reload)
        self.__deja_vu[self.__dbname] = self
        self.__backend_pid = self.execute_query(
            "select pg_backend_pid()").fetchone()['pg_backend_pid']

    reconnect = __connect

    def _reload(self, config_file=None):
        "Reload metadata"
        self.__connect(config_file, True)

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

    def _fields_metadata(self, sfqrn):
        "Proxy to PgMeta.fields_meta"
        return self.__pg_meta.fields_meta(self.__dbname, sfqrn)

    def _fkeys_metadata(self, sfqrn):
        "Proxy to PgMeta.fkeys_meta"
        return self.__pg_meta.fkeys_meta(self.__dbname, sfqrn)

    def _relation_metadata(self, fqrn):
        "Proxy to PgMeta.relation_meta"
        return self.__pg_meta.relation_meta(self.__dbname, fqrn)

    def _unique_constraints_list(self, fqrn):
        "Proxy to PgMeta._unique_constraints_list"
        return self.__pg_meta._unique_constraints_list(self.__dbname, fqrn)

    def _pkey_constraint(self, fqrn):
        "Proxy to PgMeta._pkey_constraint"
        return self.__pg_meta._pkey_constraint(self.__dbname, fqrn)

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

    def has_relation(self, qtn):
        """Checks if the qtn is a relation in the database

        @qtn is in the form "<schema>".<table>
        Returns True if the relation exists, False otherwise.
        Also works for views and materialized views.
        """
        return self.__pg_meta.has_relation(self.__dbname, *qtn.rsplit('.', 1))

    @classmethod
    def _check_deja_vu_class(cls, dbname, schema, relation):
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
