#-*- coding: utf-8 -*-
# pylint: disable=protected-access

"""This module provides the Field class."""

from psycopg2.extensions import register_adapter, adapt

from half_orm.null import NULL

class Field():
    """The class Field is for Relation internal usage. It is called by
    the RelationFactory metaclass for each field in the relation considered.
    """
    def __init__(self, name, relation, metadata):
        self.__relation = relation
        self.__name = name
        self.__is_set = False
        self.__metadata = metadata
        self.__value = None
        self.__unaccent = False
        self.__comp = '='

    @property
    def _relation(self):
        return self.__relation

    def is_set(self):
        "Returns if the field is set or not."
        return self.__is_set

    def is_pk(self):
        "Returns True if the field is part of the PK"
        return bool(self.__metadata['pkey'])

    def is_unique(self):
        "Returns True if the field is defined as unique"
        return bool(self.__metadata['uniq'])

    def is_not_null(self):
        "Returns True if the field is defined as not null."
        return bool(self.__metadata['notnull'])

    def __repr__(self):
        md_ = self.__metadata
        repr_ = "({}) {}".format(
            md_['fieldtype'], md_['pkey'] and 'PK' or ('{}{}'.format(
                md_['uniq'] and 'UNIQUE ' or '',
                md_['notnull'] and 'NOT NULL' or '')))
        if self.__is_set:
            repr_ = "{} ({} {} {})".format(
                repr_, self.__name, self.__comp, self.__value)
        return repr_.strip()

    def __str__(self):
        return str(self.__value)

    def _praf(self, query, id_):
        """Returns field_name prefixed with relation alias if the query is
        select. Otherwise, returns the field name quoted with ".
        """
        id_ = 'r{}'.format(id_)
        if query == 'select':
            return '{}."{}"'.format(id_, self.__name)
        return '"{}"'.format(self.__name)

    def where_repr(self, query, id_):
        """Returns the SQL representation of the field for the where clause
        """
        where_repr = ''
        comp_str = '%s'
        comp = self.comp()
        if comp == '@@':
            comp_str = 'websearch_to_tsquery(%s)'
        if isinstance(self.__value, (list, tuple)):
            if self.type_[0] != '_': # not an array type
                comp_str = 'any(%s)'
                if comp == '@@':
                    comp_str = 'any(websearch_to_tsquery(%s))'
        if not self.unaccent:
            where_repr = "{} {} {}".format(
                self._praf(query, id_), comp, comp_str)
        else:
            where_repr = "unaccent({}) {} unaccent({})".format(
                self._praf(query, id_), comp, comp_str)
        return where_repr

    @property
    def value(self):
        "Returns the value of the field object"
        return self.__value

    def set(self, *args):
        "Sets the value of the field object"
        self.__set__(self.__relation, *args)

    def __set__(self, obj, *args):
        """Sets the value (and the comparator) associated with the field."""
        if len(args) == 1:
            value = args[0]
            if value is None:
                self.unset()
                return
            comp = None
            self.__relation = obj
            if isinstance(value, tuple):
                if len(value) != 2:
                    raise ValueError(f"Can't match {value} with (comp, value)!")
                comp, value = value
            if value is NULL and comp is None:
                comp = 'is'
            elif comp is None:
                comp = '='
        elif len(args) == 2:
            # The first argument IS comp.
            comp, value = args
            if value is None:
                raise ValueError("Can't have a None value with a comparator!")
        else:
            raise RuntimeError('')
        if value is NULL:
            if not comp in {'is', 'is not'}:
                raise ValueError("comp should be 'is' or 'is not' with NULL value!")
        self.__is_set = True
        self.__value = value
        self.__comp = comp

    def unset(self):
        "Unset a field"
        self.__is_set = False
        self.__value = None
        self.__comp = '='

    @property
    def type_(self):
        "Returns the SQL type of the field"
        return self.__metadata['fieldtype']

    def __get_unaccent(self):
        return self.__unaccent
    def __set_unaccent(self, value):
        if not isinstance(value, bool):
            raise RuntimeError('unaccent argument must be of boolean type!')
        self.__unaccent = value

    unaccent = property(__get_unaccent, __set_unaccent)

    def comp(self):
        "Returns the comparator associated to the value."
        if self.__comp == '%':
            return '%%'
        return self.__comp

    @property
    def relation(self):
        """Returns the relation for which self is an attribute."""
        return self.__relation

    def _psycopg_adapter(self):
        """Return the SQL representation of self.__value"""
        return adapt(self.__value)

register_adapter(Field, Field._psycopg_adapter)
