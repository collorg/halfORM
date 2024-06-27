#-*- coding: utf-8 -*-
# pylint: disable=protected-access

"""This module provides the Field class. It is used by the `relation <#module-half_orm.relation>`_ module."""

import psycopg2
import sys
from numbers import Number

from half_orm.null import NULL
from half_orm.sql_adapter import SQL_ADAPTER

class Field():
    """The class Field is for Relation internal usage. It is called by
    the RelationFactory metaclass for each field in the relation considered.
    """
    def __init__(self, name, relation, metadata):
        self._relation = relation
        self._name = name
        self._is_set = False
        self._metadata = metadata
        self._sql_type = self._metadata['fieldtype']
        self._value = None
        self._value_is_field = False
        self._unaccent = False
        self._comp = '='

    def is_set(self):
        "Returns if the field is set or not."
        return self._is_set

    def value_is_field(self):
        return self._value_is_field

    def _is_part_of_pk(self):
        "Returns True if the field is part of the PK"
        return bool(self._metadata['pkey'])

    def is_not_null(self):
        "Returns True if the field is defined as not null."
        return bool(self._metadata['notnull'])

    def __repr__(self):
        md_ = self._metadata
        field_constraint = f"{md_['notnull'] and 'NOT NULL' or ''}"
        repr_ = f"({md_['fieldtype']}) {field_constraint}"
        if self._is_set:
            repr_ = f"{repr_} ({self._name} {self._comp} {self._value})"
        return repr_.strip()

    def __str__(self):
        return str(self._value)

    def _praf(self, query, ho_id):
        """Returns field_name prefixed with relation alias if the query is
        select. Otherwise, returns the field name quoted with ".
        """
        ho_id = f'r{ho_id}'
        if query == 'select':
            return f'{ho_id}."{self._name}"'
        return f'"{self._name}"'

    def _where_repr(self, query, ho_id):
        """Returns the SQL representation of the field for the where clause
        """
        where_repr = ''
        comp_str = '%s'
        comp = self._comp
        if comp == '@@':
            comp_str = 'websearch_to_tsquery(%s)'
        if isinstance(self._value, (list, tuple)) and self._sql_type[0] != '_': # not an array type
            comp_str = 'any(%s)'
            if comp == '@@':
                comp_str = 'any(websearch_to_tsquery(%s))'
        if issubclass(self._value.__class__, Field):
            comp_str = self._value._praf(query, ho_id)
        if not self.unaccent:
            where_repr = f"{self._praf(query, ho_id)} {comp} {comp_str}"
        else:
            where_repr = f"unaccent({self._praf(query, ho_id)}) {comp} unaccent({comp_str})"
        return where_repr

    @property
    def value(self):
        "Returns the value of the field object"
        return self._value

    def set(self, *args):
        """Sets the value (and the comparator) associated with the field."""
        self._relation._ho_is_singleton = False
        value = args[0]
        if value is None:
            self._unset()
            return
        comp = None
        if isinstance(value, tuple):
            if len(value) != 2:
                raise ValueError(f"Can't match {value} with (comp, value)!")
            comp, value = value
        if value is None:
            raise ValueError("Can't have a None value with a comparator!")
        if value is NULL and comp is None:
            comp = 'is'
        elif comp is None:
            comp = '='
        comp = comp.lower()
        if value is NULL and comp not in {'is', 'is not'}:
            raise ValueError("comp should be 'is' or 'is not' with NULL value!")
        self._is_set = True
        if isinstance(value, Field):
            self._value_is_field = True
        self._value = value
        self._comp = comp
        if self._comp == '%':
            self._comp = '%%'


    def _set(self, *args):
        sys.stderr.write(
            "WARNING! Field._set method is deprecated. Use Field.set instead.\n"
            "It will be remove in 1.0 version.\n")
        return self.set(*args)

    def _unset(self):
        "Unset a field"
        self._is_set = False
        self._value = None
        self._value_is_field = False
        self._comp = '='

    @property
    def unaccent(self):
        return self._unaccent
    @unaccent.setter
    def unaccent(self, value):
        if not isinstance(value, bool):
            raise RuntimeError('unaccent value must be True or False!')
        self._unaccent = value

    def _psycopg_adapter(self):
        """Return the SQL representation of self._value"""
        return psycopg2.extensions.adapt(self._value)

    def __call__(self):
        """In case someone inadvertently uses the name of a field for a method."""
        rel_class = self._relation.__class__
        rcn = rel_class.__name__
        method = rel_class.__dict__.get(self._name)
        err_msg = "'Field' object is not callable."
        warn_msg = f"'{self._name}' is an attribute of type Field of the '{rcn}' object."
        if method:
            err_msg = f"{err_msg}\n{warn_msg}"
            err_msg = f"{err_msg}\nDo not use '{self._name}' as a method name."
        raise TypeError(err_msg)

psycopg2.extensions.register_adapter(Field, Field._psycopg_adapter)
psycopg2.extensions.register_adapter(dict, psycopg2.extras.Json)
