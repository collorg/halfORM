#-*- coding: utf-8 -*-
# pylint: disable=protected-access

"""This module provides the Field class."""

from psycopg2.extensions import register_adapter, adapt

from half_orm.field_interface import FieldInterface
from half_orm.null import NULL

class Field(FieldInterface):
    """The class Field is for Relation internal usage. It is called by
    the RelationFactory metaclass for each field in the relation considered.
    """
    def __init__(self, name, metadata):
        self._relation = None
        self.__metadata = metadata
        self._value = None #FIXME should be __value but __set__ doesn't work!
        self.__unaccent = False
        self.__comp = '='
        super().__init__(name)

    def __repr__(self):
        md_ = self.__metadata
        repr_ = "({}) {}".format(
            md_['fieldtype'], md_['pkey'] and 'PK' or ('{}{}'.format(
                md_['uniq'] and 'UNIQUE ' or '',
                md_['notnull'] and 'NOT NULL' or '')))
        if self._is_set:
            repr_ = "{} ({} {} {})".format(
                repr_, self.name(), self.__comp, self._value)
        return repr_.strip()

    def __str__(self):
        return str(self._value)

    def _praf(self, query, id_):
        """Returns field_name prefixed with relation alias if the query is
        select. Otherwise, returns the field name quoted with ".
        """
        id_ = 'r{}'.format(id_)
        if query == 'select':
            return '{}.{}'.format(id_, self.name())
        return '"{}"'.format(self.name())

    def where_repr(self, query, id_):
        """Returns the SQL representation of the field for the where clause
        """
        where_repr = ''
        comp_str = '%s'
        if isinstance(self._value, (list, tuple)):
            if self.type_[0] != '_': # not an array type
                comp_str = 'any(%s)'
        if not self.unaccent:
            where_repr = "{} {} {}".format(
                self._praf(query, id_), self.comp(), comp_str)
        else:
            where_repr = "unaccent({}) {} unaccent({})".format(
                self._praf(query, id_), self.comp(), comp_str)
        return where_repr

    @property
    def value(self):
        "Returns the value of the field object"
        return self._value

    def set(self, value):
        "Sets the value of the field object"
        self.__set__(self._relation, value)

    def __set__(self, obj, value):
        """Sets the value (and the comparator) associated with the field."""
        if value is None:
            # None is not a value use Null class to set to Null
            return
        comp = None
        self._relation = obj
        is_field = isinstance(value, Field)
        if isinstance(value, tuple):
            assert len(value) == 2
            comp, value = value
        if value is NULL and comp is None:
            comp = 'is'
        if value is NULL:
            assert comp == 'is' or comp == 'is not'
        elif comp is None:
            if not is_field:
                comp = '='
            else:
                value.from_ = value._relation
                value.to_ = self._relation
                value.to_._joined_to.insert(0, (value.from_, value))
                value.fields = [value.name()]
                value.fk_names = [self.name()]
                comp = 'in'
        if not is_field:
            self._is_set = True
        self._value = value
        self.__comp = comp

    @property
    def type_(self):
        "Returns the SQL type of the field"
        return self.__metadata['fieldtype']

    def __get_unaccent(self):
        return self.__unaccent
    def __set_unaccent(self, value):
        assert isinstance(value, bool)
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
        return self._relation

    def _psycopg_adapter(self):
        """Return the SQL representation of self._value"""
        return adapt(self._value)

register_adapter(Field, Field._psycopg_adapter)
