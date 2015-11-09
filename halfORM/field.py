#-*- coding: utf-8 -*-
# pylint: disable=protected-access

"""This module provides the Field class."""

from psycopg2.extensions import register_adapter, adapt

class Field():
    """The class Field is for Relation internal usage. It is called by
    the RelationFactory metaclass for each field in the relation considered.
    """
    __slots__ = [
        '__name', '__metadata', '__is_set', '__value', '__comp', '__relation'
    ]
    def __init__(self, name, metadata):
        self.__name = name
        self.__relation = None
        self.__metadata = metadata
        self.__is_set = False
        self.__value = None
        self.__comp = '='

    def __repr__(self):
        md_ = self.__metadata
        repr_ = "({}) {}".format(
            md_['fieldtype'], md_['pkey'] and 'PK' or ('{}{}'.format(
                md_['uniq'] and 'UNIQUE ' or '',
                md_['notnull'] and 'NOT NULL' or '')))
        if self.__is_set:
            repr_ = "{} ({} {} {})".format(
                repr_, self.__name, self.__comp, self.__value)
        return repr_

    def __str__(self):
        return str(self.__value)

    def name(self):
        """This property returns the name of the field."""
        return self.__name

    def is_set(self):
        "This property returns a boolean indicating if the field is set of not."
        return self.__is_set

    @property
    def value(self):
        "Returns the value of the field object"
        return self.__value

    def __set__(self, obj, value):
        """Sets the value (and the comparator) associated with the field."""
        comp = None
        is_field = value.__class__ == self.__class__
        if isinstance(value, tuple):
            assert len(value) == 2
            value, comp = value
        if value is None and comp is None:
            comp = 'is'
        if value is None:
            assert comp == 'is' or comp == 'is not'
        elif comp is None:
            if not is_field:
                comp = '='
            else:
                comp = 'in'
        self.__is_set = True
        self.__value = value
        self.__comp = comp

    def comp(self):
        "This property returns the comparator associated with the value."
        return self.__comp

    @property
    def relation(self):
        """Returns the relation for which self is an attribute."""
        return self.__relation

    def __set_relation(self, relation):
        """Sets the relation for which self is an attribute."""
        self.__relation = relation

    def _psycopg_adapter(self):
        """Return the SQL representation of self.__value"""
        return adapt(self.__value)

register_adapter(Field, Field._psycopg_adapter)
