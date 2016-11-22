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
        self._cast = None
        super(FKey, self).__init__(fk_name, fk_names, fields)

    def __get_fk_qrn(self):
        """Returns QRN from FQRN."""
        return '.'.join(self.__fk_fqrn.split('.', 1)[1:])

    def cast(self, qrn):
        """Cast the fkey to another relation (usefull with inheritance)
        """
        self._cast = qrn

    def __call__(self, **kwargs):
        """Returns the relation on which the fkey is defined.
        If model._scope is set, instanciate the class from the scoped module.
        Uses the _cast if it is set.
        """
        model = self._relation._model
        f_qrn = self.__get_fk_qrn()
        if model._scope:
            f_class = model._import_class(self._cast or f_qrn)
        else:
            f_class = model.get_relation_class(f_qrn)
        f_relation = f_class(**kwargs)
        rev_fkey_name = '__reverse_{}'.format(
            f_relation._fqrn.replace(".", "_"))
        f_relation.fkeys = {
            rev_fkey_name: FKey(
                rev_fkey_name,
                f_relation._fqrn.split('.'), self._fields, self._fk_names)}
        _ = {fkey._set_relation(f_relation)
             for fkey in f_relation.fkeys.values()}
        f_relation.fkeys[rev_fkey_name].set(self._relation)
        return f_relation

    def set(self, to_):
        self.__set__(self._relation, to_)

    def __set__(self, from_, to_):
        """Sets the value associated with the foreign key.

        The value must be an object of type Relation having the
        same FQRN that (or inheriting) the one referenced by self.__fk_fqrn.
        """
        try:
            assert hasattr(to_, '_is_half_orm_relation')
        except AssertionError:
            raise Exception("Expecting a Relation")
        to_classes = set(type.mro(to_.__class__))
        self_classes = set(type.mro(self._relation.__class__))
        common_classes = to_classes.intersection(self_classes)
        object in common_classes and common_classes.remove(object)
        if (not common_classes):
            raise Exception(
                "Type mismatch:\n{} != {}".format(self.__fk_fqrn, to_._fqrn))
        self.from_ = from_
        self.to_ = to_
        self._is_set = to_.is_set()
        deja_vu = False
        for rel, fkey in from_._joined_to:
            if id(rel) == id(to_):
                deja_vu = True
                break
        if not deja_vu:
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
