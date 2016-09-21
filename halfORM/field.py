#-*- coding: utf-8 -*-
# pylint: disable=protected-access

"""This module provides the Field class."""

from halfORM.fkey_interface import FKeyInterface
from psycopg2.extensions import register_adapter, adapt

class Field(FKeyInterface):
    """The class Field is for Relation internal usage. It is called by
    the RelationFactory metaclass for each field in the relation considered.
    """
    def __init__(self, name, metadata):
        self.__relation = None
        self.__metadata = metadata
        self.__value = None
        self.__unaccent = False
        self.__comp = '='
        super(Field, self).__init__(name)

    def __repr__(self):
        md_ = self.__metadata
        repr_ = "({}) {}".format(
            md_['fieldtype'], md_['pkey'] and 'PK' or ('{}{}'.format(
                md_['uniq'] and 'UNIQUE ' or '',
                md_['notnull'] and 'NOT NULL' or '')))
        if self._is_set:
            repr_ = "{} ({} {} {})".format(
                repr_, self.name(), self.__comp, self.__value)
        return repr_

    def __str__(self):
        return str(self.__value)

    @property
    def value(self):
        "Returns the value of the field object"
        return self.__value

    def __get_unaccent(self):
        return self.__unaccent
    def __set_unaccent(self, value):
        assert type(value) == bool
        self.__unaccent = value

    unaccent = property(__get_unaccent, __set_unaccent)

    def __set__(self, obj, value):
        """Sets the value (and the comparator) associated with the field."""
        comp = None
        self.__relation = obj
        is_field = isinstance(value, Field)
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
                value.from_ = value.__relation
                value.to_ = self.__relation
                value.to_._joined_to.insert(0, (value.from_, value))
                value.fields = [value.name()]
                value.fk_names = [self.name()]
                comp = 'in'
        if not is_field:
            self._is_set = True
        self.__value = value
        self.__comp = comp

    def comp(self):
        "Returns the comparator associated to the value."
        return self.__comp

    @property
    def relation(self):
        """Returns the relation for which self is an attribute."""
        return self.__relation

    def _set_relation(self, relation):
        """Sets the relation for which self is an attribute."""
        self.__relation = relation

    def _psycopg_adapter(self):
        """Return the SQL representation of self.__value"""
        return adapt(self.__value)

register_adapter(Field, Field._psycopg_adapter)
