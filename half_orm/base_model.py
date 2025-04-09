# half_orm/base_model.py

import importlib
import os
import sys
import typing
from typing import Optional
from configparser import ConfigParser
from os import environ

from . import model_errors
from . import pg_meta
from .relation_factory import factory

CONF_DIR = os.path.abspath(environ.get('HALFORM_CONF_DIR', '/etc/half_orm'))

class BaseModel:
    _classes_ = {}
    _deja_vu = {}
    def __init__(self, config_file: str, scope: str = None):
        self._dbinfo = {}
        self._load_config(config_file)
        self._scope = scope and scope.split('.')[0]
        self.__conn = None
        self._pg_meta = None

    def _load_config(self, config_file):
        """Load the config file

        Raises:
            MissingConfigFile: If the **config_file** is not found in *HALFORM_CONF_DIR*.
            MalformedConfigFile: if the *name* is missing in the **config_file**.
            RuntimeError: If the reconnection is attempted on another database.
        """
        self.__config_file = config_file
        config = ConfigParser()
        file_ = os.path.join(CONF_DIR, self.__config_file)
        if not config.read([file_]):
            raise model_errors.MissingConfigFile(file_)
        try:
            database = config['database']
        except KeyError as exc:
            raise model_errors.MalformedConfigFile(file_, 'Missing section', 'database') from exc
        try:
            dbname = database['name']
        except KeyError as exc:
            raise model_errors.MalformedConfigFile(file_, 'Missing mandatory parameter', 'name') from exc

        if self._dbinfo and config_file and dbname != self._dbname:
            raise RuntimeError(
                f"Can't reconnect to another database: {dbname} != {self._dbname}")

        self._dbinfo['dbname'] = dbname
        self._dbinfo['user'] = database.get('user')
        self._dbinfo['password'] = database.get('password')
        self._dbinfo['host'] = database.get('host')
        self._dbinfo['port'] = database.get('port')

    @property
    def _dbname(self):
        return self._dbinfo['dbname']


    def get_relation_class(self, relation_name: str, fields_aliases: typing.Dict=None): # -> Relation
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
        try:
            schema, table = relation_name.replace('"', '').rsplit('.', 1)
        except ValueError as err:
            raise model_errors.MissingSchemaInName(relation_name) from err
        return factory({'fqrn': (self._dbname, schema, table), 'model': self._deja_vu[self._dbname], 'fields_aliases':fields_aliases})

    def _fields_metadata(self, sfqrn):
        "Proxy to PgMeta.fields_meta"
        return self._pg_meta.fields_meta(self._dbname, sfqrn)

    def _fkeys_metadata(self, sfqrn):
        "Proxy to PgMeta.fkeys_meta"
        return self._pg_meta.fkeys_meta(self._dbname, sfqrn)

    def _relation_metadata(self, fqrn):
        "Proxy to PgMeta.relation_meta"
        return self._pg_meta.relation_meta(self._dbname, fqrn)

    def _unique_constraints_list(self, fqrn):
        "Proxy to PgMeta._unique_constraints_list"
        return self._pg_meta._unique_constraints_list(self._dbname, fqrn)

    def _pkey_constraint(self, fqrn):
        "Proxy to PgMeta._pkey_constraint"
        return self._pg_meta._pkey_constraint(self._dbname, fqrn)

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
        return self._pg_meta.has_relation(self._dbname, *qtn.rsplit('.', 1))

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
        return self._pg_meta.desc(self._dbname)

    def __str__(self):
        return self._pg_meta.str(self._dbname)

    def classes(self):
        "Returns the all the classes of the model"
        for relation in self._relations():
            package_name = relation[1][0]
            module_name = ".".join(relation[1][1:])
            if module_name.find('half_orm_meta') == 0:
                continue
            class_name = pg_meta.camel_case(relation[1][-1])
            module = importlib.import_module(f".{module_name}", package_name)
            yield getattr(module, class_name), relation[0]
