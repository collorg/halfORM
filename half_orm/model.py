#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""This module provides the class Model.

The class Model is responsible for the connection to the PostgreSQL database.
    
Once connected, you can use the
`get_relation_class <#half_orm.model.Model.get_relation_class>`_
method to generate a class to access any relation (table/view) in your database.

Example:
    >>> from half_orm.model import Model
    >>> model = Model('my_config_file')
    >>> class MyTable(model.get_relation_class('my_schema.my_table')):
    ...     # Your business code goes here

Note:
    The default schema is ``public`` in PostgreSQL, so to reference a table
    ``my_table`` in this schema you'll have to use ``pubic.my_table``.
"""


import os
import sys
from configparser import ConfigParser
from os import environ
from functools import wraps
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Generator, List

from half_orm.model_errors import MalformedConfigFile, MissingConfigFile, MissingSchemaInName, UnknownRelation
from half_orm.relation import Relation, REL_INTERFACES, REL_CLASS_NAMES
from half_orm import pg_meta
from half_orm.packager import utils

CONF_DIR = os.path.abspath(environ.get('HALFORM_CONF_DIR', '/etc/half_orm'))


psycopg2.extras.register_uuid()

def deprecated(fct):
    @wraps(fct)
    def wrapper(self, *args, **kwargs):
        name = fct.__name__
        dep_name = fct.__name__[0:3] == 'ho_' and fct.__name__[3:] or f'_{fct.__name__[4:0]}'
        sys.stderr.write(
            f'HalfORM WARNING! "{utils.Color.bold(dep_name)}" is deprecated. '
            'It will be removed in half_orm 1.0.\n'
            f'Use "{utils.Color.bold(name)}" instead.\n'
            )
        return fct(self, *args, **kwargs)
    return wrapper

class Model:
    """
    Parameters:
        config_file (str): the configuration file that contains the informations to connect
            to the database.
        scope (Optional[str]): used to agregate several modules in a package.
            See `half_orm_packager <https://github.com/collorg/halfORM_packager>`_.

    Note:
        The **config_file** is searched in the `HALFORM_CONF_DIR` variable if specified,
        then in `/etc/half_orm`. The file format is as follows:

            | [database]
            | name = <postgres db name>
            | user = <postgres user>
            | password = <postgres password>
            | host = <host name | localhost>
            | port = <port | 5432>

        *name* is the only mandatory entry if you are using an
        `ident login with a local account <https://www.postgresql.org/docs/current/auth-ident.html>`_.
    """
    __deja_vu = {}
    _classes_ = {}
    def __init__(self, config_file: str, scope: str=None):
        """Model constructor

        Use @config_file in your scripts. The @dbname parameter is
        reserved to the __factory metaclass.
        """
        self.__backend_pid = None
        self.__config_file = config_file
        self.__dbinfo = {}
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

            A prefered way to create a class:
                >>> class Person(model.get_relation_class('actor.person)):
                >>>     # Your code goes here

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
            tbl_attr['_qrn'] = pg_meta.normalize_qrn(dct['fqrn'])

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
            tbl_attr['_fqrn'] = pg_meta.normalize_fqrn(dct['fqrn'])
            tbl_attr['__kind'] = REL_CLASS_NAMES[metadata['tablekind']]
            tbl_attr['_fkeys'] = []
            for fct_name, fct in REL_INTERFACES[metadata['tablekind']].items():
                tbl_attr[fct_name] = fct
                dep_fct_name = None
                if fct_name[0:3] == 'ho_':
                    dep_fct_name = fct_name[3:]
                    # print('XXX', fct_name, dep_fct_name)
                if fct_name[0:4] == '_ho_':
                    dep_fct_name = f'_{fct_name[4:]}'
                    # print('XXX', fct_name, dep_fct_name)
                if dep_fct_name:
                    tbl_attr[dep_fct_name] = deprecated(fct)
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

    def __connect(self, config_file: str=None, reload: bool=False):
        """Setup a new connection to the database.

        The reconnect method is an alias to the ``__connect`` method.

        Parameters:
            config_file (str): If a config_file is provided, the connection is made with the new
                parameters, allowing to change role. The database name must be the same.
            reload (bool): If set to True, reloads the metadata from the database. Usefull if
                the model has changed.

        Raises:
            MissingConfigFile: If the **config_file** is not found in *HALFORM_CONF_DIR*.
            MalformedConfigFile: if the *name* is missing in the **config_file**. 
            RuntimeError: If the reconnection is attempted on another database.
        """
        self.disconnect()
        if config_file:
            self.__config_file = config_file

        config = ConfigParser()

        if not config.read(
                [os.path.join(CONF_DIR, self.__config_file)]):
            raise MissingConfigFile(os.path.join(CONF_DIR, self.__config_file))

        params = config['database']
        if config_file and params['name'] != self.__dbname:
            raise RuntimeError(
                f"Can't reconnect to another database {params['name']} != {self.__dbname}")
        self.__dbinfo['name'] = params['name']
        self.__dbinfo['user'] = params.get('user')
        self.__dbinfo['password'] = params.get('password')
        self.__dbinfo['host'] = params.get('host')
        self.__dbinfo['port'] = params.get('port')
        self.__production = params.getboolean('production', False)
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

    @property
    def __dbname(self):
        return self.__dbinfo['name']

    def ping(self):
        """Checks if the connection is still established.
        Attempts a new connection otherwise.

        Returns:
            bool: True if the connection is established, False otherwise.
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

    def disconnect(self):
        """Closes the connection to the database.
        """
        if self.__conn is not None:
            if not self.__conn.closed:
                self.__conn.close()

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
        """Executes a raw SQL query.
        
        Warning:
            This method calls the psycopg2
            `cursor.execute <https://www.psycopg.org/docs/cursor.html?highlight=execute#cursor.execute>`_
            function.
            Please read the psycopg2 documentation on
            `passing parameters to SQL queries <https://www.psycopg.org/docs/usage.html#query-parameters>`_.
        """
        cursor = self.__conn.cursor()
        cursor.execute(query, values)
        return cursor

    def execute_function(self, fct_name, *args, **kwargs) -> List[tuple]:
        """`Executes a PostgreSQL function <https://www.postgresql.org/docs/current/sql-syntax-calling-funcs.html>`_.

        Arguments:
            *args: The list of parameters to be passed to the postgresql function.
            **kwargs: The list of named parameters to be passed to the postgresql function.

        Returns:
            List[tuple]: a list of tuples.
        
        Raises:
            RuntimeError: If you mix ***args** and ****kwargs**.

        Note:
            You can't mix args and kwargs with the execute_function method!
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
        """`Executes a PostgreSQL procedure <https://www.postgresql.org/docs/current/sql-call.html>`_.

        Arguments:
            *args: The list of parameters to be passed to the postgresql function.
            **kwargs: The list of named parameters to be passed to the postgresql function.

        Returns:
            None | List[tuple]: None or a list of tuples.
        
        Raises:
            RuntimeError: If you mix ***args** and ****kwargs**.

        Note:
            You can't mix args and kwargs with the call_procedure method!
        """
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

    def has_relation(self, qtn: str) -> bool:
        """Checks if the qtn is a relation in the database

        Returns:
            bool: True if the relation exists in the database, False otherwise.

        Example:
            >>> model.has_relation('public.person')
            False
            >>> model.has_relation('actor.person')
            True
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
        self._scope = scope or self._scope
        module_path = ".".join(t_qtn)
        if self._scope:
            module_path = f'{self._scope}.{module_path}'
        _class_name = pg_meta.class_name(qtn) # XXX
        module = __import__(
            module_path, globals(), locals(), [_class_name], 0)
        print(dir(module))
        return module.__dict__[_class_name]

    def _relations(self):
        """List all_ the relations in the database"""
        rels = self.__pg_meta.relations_list(self.__dbname)
        return rels

    def desc(self):
        """Returns the list of the relations of the model.

        Each element in the list contains:

        * the relation type: 'r' relation, 'v' view, 'm' materialized view, 'p' partition;
        * a tuple identifying the relation: (db name>, <schema name>, <relation name>);
        * a list of tuples indentifying the inherited relations.

        Example:
            >>> from half_orm.model import Model
            >>> halftest = Model('halftest')
            >>> halftest.desc()
            [('r', ('halftest', 'actor', 'person'), []), ('r', ('halftest', 'blog', 'comment'), []), ('r', ('halftest', 'blog', 'event'), [('halftest', 'blog', 'post')]), ('r', ('halftest', 'blog', 'post'), []), ('v', ('halftest', 'blog.view', 'post_comment'), [])]
        """
        return self.__pg_meta.desc(self.__dbname)

    def __str__(self):
        return self.__pg_meta.str(self.__dbname)

    @property
    def production(self):
        """Returns the production status of the db. Production is set by adding
        ``production = True`` to the **config file**.

        Returns:
            bool: True if the database is in production, False otherwise
        """
        return self.__production

