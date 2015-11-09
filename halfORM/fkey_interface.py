#-*- coding: utf-8 -*-

"""This module provides the FKeyInterface class."""

class FKeyInterface():
    """Foreign key class interface

    properties shared between Fkey and Field classes
    """
    def __init__(self, name, fk_names=None, fields=None):
        self._name = name
        self._fk_names = fk_names or []
        self._fields = fields or []
        self._fk_from = None
        self._fk_to = None
        self._is_set = False

    def name(self):
        """Returns the name of the field/foreign key."""
        return self._name

    def is_set(self):
        """Returns True is the foreign key is set."""
        return self._is_set

    def __get_from(self):
        """Returns the origin of the fkey."""
        return self._fk_from
    def __set_from(self, from_):
        """Sets the origin of the fkey."""
        self._fk_from = from_
    from_ = property(__get_from, __set_from)

    def __get_to(self):
        """Returns the destination relation of the fkey."""
        return self._fk_to
    def __set_to(self, to_):
        """Sets the destination relation of the fkey."""
        self._fk_to = to_
    to_ = property(__get_to, __set_to)

    def __get_fields(self):
        """Returns the the fields of the foreign key."""
        return self._fields
    def __set_fields(self, fields):
        """Sets the the fields of the foreign key."""
        self._fields = fields
    fields = property(__get_fields, __set_fields)

    def __get_fk_names(self):
        """Returns the names of the fields in the foreign table."""
        return self._fk_names
    def __set_fk_names(self, fk_names):
        """Sets the names of the fields in the foreign table."""
        self._fk_names = fk_names
    fk_names = property(__get_fk_names, __set_fk_names)
