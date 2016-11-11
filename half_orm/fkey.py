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
        self._fk_from = None
        self._fk_to = None
        self.__fk_fqrn = ".".join(['"{}"'.format(elt) for elt in fk_sfqrn])
        super(FKey, self).__init__(fk_name, fk_names, fields)

    def __get_fk_qrn(self):
        """Returns QRN from FQRN."""
        return '.'.join(self.__fk_fqrn.split('.', 1)[1:])

    def __call__(self, **kwargs):
        """Returns the relation on which the fkey is defined."""
        f_relation = self._relation._model.get_relation_class(
            self.__get_fk_qrn())(**kwargs)
        f_relation.fkeys = {
            '__reverse': FKey(
                '__reverse',
                f_relation._fqrn.split('.'), self._fields, self._fk_names)}
        _ = {fkey._set_relation(f_relation)
             for fkey in f_relation.fkeys.values()}
        f_relation.fkeys['__reverse'].set(self._relation)
        return f_relation
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

        if to_ is None:
            to_ = self._relation(self.__get_fk_qrn())
        to_classes = set(type.mro(to_.__class__))
        object in to_classes and to_classes.remove(object)
        self_classes = set(type.mro(self._relation.__class__))
        object in self_classes and self_classes.remove(object)
        common_classes = to_classes.intersection(self_classes)
        if (not common_classes or not
                hasattr(list(common_classes)[0], '_is_half_orm_relation')):
            raise Exception("Expecting a Relation")
        #TODO deal with inheritance
        # if the fqrn differ, we verify that
        # model.relation(self.__fk_fqrn) inherits to_
        if False and not self.__fk_fqrn == to_._fqrn:
            raise Exception(
                "Relations must be of the same type\n{} != {}".format(
                    self.__fk_fqrn, to_._fqrn))
        self.from_ = from_
        self.to_ = to_
        self._is_set = to_.is_set()
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
