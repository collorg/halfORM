#-*- coding: utf-8 -*-
# pylint: disable=protected-access

"""This module provides the FKey class."""

from half_orm.field_interface import FieldInterface

class FKey(FieldInterface):
    """Foreign key class

    A foreign key is set by assigning to it a Relation object of the
    corresponding type (see FKey.set method).
    It is then used to construct the join query for Relation.select
    method.
    """
    def __init__(self, fk_name, fk_sfqrn, fk_names, fields):
        self._relation = None
        self.__fk_fqrn = ".".join(['"{}"'.format(elt) for elt in fk_sfqrn])
        super(FKey, self).__init__(fk_name, fk_names, fields)

    def __get__(self, obj, type_=None):
        """Returns the relation on which the fkey is defined."""
        if self.from_ is None:
            self.__set__(obj)
            if not (self.from_, self) in self.to_._joined_to:
                self.to_._joined_to.insert(0, (self.from_, self))
        return self.to_

    def set(self, to_):
        self.__set__(self._relation, to_)

    def __set__(self, from_, to_=None):
        """Sets the value associated with the foreign key.

        The value must be and object of type Relation having the
        same FQRN as referenced by self.__fk_fqrn.
        """
        def __get_qrn(fqrn):
            """Returns QRN from FQRN."""
            return '.'.join(fqrn.split('.', 1)[1:])

        if to_ is None:
            to_ = self._relation(__get_qrn(self.__fk_fqrn))
        if not isinstance(to_, self._relation.__class__.__bases__[0]):
            raise Exception("Expecting a Relation")
        #TODO deal with inheritance
        # if the fqrn differ, we verify that
        # model.relation(self.__fk_fqrn) inherits to_
        if False and not self.__fk_fqrn == to_.fqrn:
            raise Exception(
                "Relations must be of the same type\n{} != {}".format(
                    self.__fk_fqrn, to_.fqrn))
        self.from_ = from_
        self.to_ = to_
        self._is_set = True
        if not (to_, self) in from_._joined_to:
            from_._joined_to.insert(0, (to_, self))

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

    @property
    def fk_fqrn(self):
        """Returns the FQRN of the relation pointed to."""
        return self.__fk_fqrn

    def __repr__(self):
        """Representation of a foreign key
        """
        fields = '({})'.format(', '.join(self.fields))
        repr_ = u"- {}: {}\n ↳ {}({})".format(
            self.name(),
            fields, self.__fk_fqrn, ', '.join(self.fk_names))
        if self._is_set:
            repr_value = str(self.to_)
            res = []
            for line in repr_value.split('\n'):
                res.append('     {}'.format(line))
            repr_ = '{}\n{}'.format(repr_, '\n'.join(res))
        return repr_
