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

import sys

import psycopg
from psycopg import Connection

from half_orm import pg_meta
from .base_model import BaseModel

class Model(BaseModel):
    """
    Parameters:
        config_file (str): the configuration file that contains the informations to connect
            to the database.
        scope (Optional[str]): used to agregate several modules in a package.
            See `hop <https://github.com/collorg/halfORM/blob/main/doc/hop.md>`_.

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
    def __init__(self, config_file: str, scope: str=None):
        """Model constructor

        Use @config_file in your scripts. The @dbname parameter is
        reserved to the __factory metaclass.
        """
        super().__init__(config_file, scope)
        self.__conn: Connection = None
        self.__connect()

    def __connect(self, config_file: str=None, reload: bool=False):
        """Setup a new connection to the database.

        The reconnect method is an alias to the ``__connect`` method.

        Parameters:
            config_file (str): If a config_file is provided, the connection is made with the new
                parameters, allowing to change role. The database name must be the same.
            reload (bool): If set to True, reloads the metadata from the database. Usefull if
                the model has changed.
        """
        self.disconnect()

        if config_file:
            self._load_config(config_file)

        self.__conn = psycopg.connect(**self._dbinfo, row_factory=psycopg.rows.dict_row)
        self.__conn.autocommit = True
        self._pg_meta = pg_meta.PgMeta(self.__conn, reload)
        if reload:
            self._classes_[self._dbname] = {}
        if self._dbname not in self.__class__._deja_vu:
            self._deja_vu[self._dbname] = self

    reconnect = __connect


    def ping(self):
        """Checks if the connection is still established.
        Attempts a new connection otherwise.

        Returns:
            bool: True if the connection is established, False otherwise.
        """
        try:
            self.execute_query("select 1")
            return True
        except (psycopg.errors.OperationalError, psycopg.errors.InterfaceError):
            try:
                self.__connect()
                self.execute_query("select 1")
            except (psycopg.errors.OperationalError, psycopg.errors.InterfaceError) as exc: #pragma: no cover
                # log reconnection attempt failure
                sys.stderr.write(f'{exc}\n')
                sys.stderr.flush()
            return False

    def disconnect(self):
        """Closes the connection to the database.
        """
        if self.__conn is not None and not self.__conn.closed:
            self.__conn.close()

    def _reload(self, config_file=None):
        """Reload metadata

        Updates the model according to changes made to the database.
        """
        self.__connect(config_file, True)

    @property
    def _connection(self) -> Connection:
        """\
        Property. Returns the psycopg2 connection attached to the Model object.
        """
        return self.__conn


    def execute_query(self, query, values=()):
        """Executes a raw SQL query.

        Warning:
            This method calls the psycopg2
            `cursor.execute <https://www.psycopg.org/docs/cursor.html?highlight=execute#cursor.execute>`_
            function.
            Please read the psycopg2 documentation on
            `passing parameters to SQL queries <https://www.psycopg.org/docs/usage.html#query-parameters>`_.
        """
        cursor = self.__conn.cursor(row_factory=psycopg.rows.dict_row)
        try:
            cursor.execute(query, values)
        except (psycopg.errors.OperationalError, psycopg.errors.InterfaceError):
            self.ping()
            cursor = self.__conn.cursor(row_factory=psycopg.rows.dict_row)
            cursor.execute(query, values)
        return cursor

    def execute_function(self, func_name: str, *args, **kwargs):
        """Execute a PostgreSQL function and return its result.
        Handles both scalar and set-returning functions."""
        if bool(args) and bool(kwargs):
            raise RuntimeError("You can't mix args and kwargs with the execute_function method!")
        
        with psycopg.ClientCursor(self.__conn) as cursor:
            if kwargs:
                params = ', '.join(f"%({k})s" for k in kwargs.keys())
                query = f"SELECT * FROM {func_name}({params})"
                cursor.execute(query, kwargs)
            else:
                params = ', '.join(['%s' for _ in args])
                query = f"SELECT * FROM {func_name}({params})"
                cursor.execute(query, args)
            
            try:
                return cursor.fetchall()
            except psycopg.ProgrammingError:
                # Void function or no results
                return None

    def call_procedure(self, proc_name: str, *args, **kwargs):
        """Call a stored procedure (no results expected)."""
        if bool(args) and bool(kwargs):
            raise RuntimeError("You can't mix args and kwargs with the call_procedure method!")
        
        with psycopg.ClientCursor(self.__conn) as cursor:
            if kwargs:
                params = ', '.join(f"%({k})s" for k in kwargs.keys())
                query = f"CALL {proc_name}({params})"
                cursor.execute(query, kwargs)
            else:
                params = ', '.join(['%s' for _ in args])
                query = f"CALL {proc_name}({params})"
                cursor.execute(query, args)

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
        return module.__dict__[_class_name]
