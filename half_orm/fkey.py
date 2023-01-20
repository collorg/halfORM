# -*- coding: utf-8 -*-
# pylint: disable=protected-access

"""This module provides the FKey class."""

from half_orm.pg_meta import normalize_fqrn, normalize_qrn

class FKey:
    """Foreign key class

    A foreign key is set by assigning to it a Relation object of the
    corresponding type (see FKey.set method).
    It is then used to construct the join query for Relation.ho_select
    method.
    """

    def __init__(self,
                 fk_name, relation, fk_sfqrn,
                 fk_names=None, fields=None, confupdtype=None, confdeltype=None):
        self.__relation = relation
        self.__to_relation = None
        self.__name = fk_name
        self.__is_set = False
        self.__fk_names = fk_names or []
        self.__fk_from = None
        self.__fk_to = None
        self.__confupdtype = confupdtype
        self.__confdeltype = confdeltype
        self.__fk_fqrn = fk_sfqrn
        self.__fields_names = fields
        self.__fields = [f'"{name}"' for name in fields]

    def __call__(self, __cast__=None, **kwargs):
        """Returns the relation referenced by the fkey.
        If model._scope is set, instanciate the class from the scoped module.
        Uses the __cast if it is set.
        """
        model = self.__relation._model
        f_cast = None
        get_rel = model._import_class if model._scope is not None else model.get_relation_class
        if self.__name.find('_reverse_fkey_') == 0 and __cast__:
            self.__relation = get_rel(__cast__)(**self.__relation.ho_dict())
        else:
            f_cast = __cast__
        f_relation = get_rel(f_cast or normalize_qrn(self.__fk_fqrn))(**kwargs)
        rev_fkey_name = f'_reverse_{f_relation.ho_id}'
        f_relation._fkeys[rev_fkey_name] = FKey(
            rev_fkey_name,
            f_relation,
            f_relation._t_fqrn, self.__fields, self.__fk_names)
        f_relation._fkeys[rev_fkey_name].set(self.__relation)
        return f_relation

    def values(self):
        return [list(elt.values()) for elt in self.__to_relation.ho_select(*self.__fk_names)]

    def set(self, to_):
        """Sets the relation associated to the foreign key."""
        from half_orm.relation import Relation

        self.__to_relation = to_
        from_ = self.__relation
        if not issubclass(to_.__class__, Relation):
            raise Exception("Expecting a Relation")
        to_classes = set(type.mro(to_.__class__))
        self_classes = set(type.mro(self.__relation.__class__))
        common_classes = to_classes.intersection(self_classes)
        if object in common_classes:
            common_classes.remove(object)
        if not common_classes:
            raise Exception(f"Type mismatch:\n{self.__fk_fqrn} != {to_._fqrn}")
        self.__fk_from = from_
        self.__fk_to = to_
        self.__is_set = to_.ho_is_set()
        from_._joined_to[self] = to_

    @classmethod
    def __set__(cls, *args):
        "Setting an Fkey is prohibited"
        print('XXX', cls, '\n', args)
        raise RuntimeError

    def is_set(self):
        """Return if the foreign key is set (boolean)."""
        return self.__is_set

    @property
    def to_(self):
        """Returns the destination relation of the fkey."""
        return self.__fk_to

    @to_.setter
    def to_(self, to_):
        """Sets the destination relation of the fkey."""
        self.__fk_to = to_

    @property
    def fk_fqrn(self):
        """Returns the FQRN of the relation pointed to."""
        return self.__fk_fqrn

    @property
    def confupdtype(self):
        "on update configuration"
        return self.__confupdtype

    @property
    def confdeltype(self):
        "on delete configuration"
        return self.__confdeltype

    def _join_query(self, orig_rel):
        """Returns the join_query, join_values of a foreign key.
        fkey interface: frel, from_, to_, fields, fk_names
        """
        from_ = self.__fk_from
        to_ = self.to_
        if id(from_) == id(to_):
            raise RuntimeError("You can't join a relation with itself!")
        orig_rel_id = f'r{orig_rel.ho_id}'
        to_id = f'r{to_.ho_id}'
        from_id = f'r{from_.ho_id}'
        if to_._qrn == orig_rel._qrn:
            to_id = orig_rel_id
        if from_._qrn == orig_rel._qrn:
            from_id = orig_rel_id
        from_fields = (f'{from_id}.{name}' for name in self.__fields)
        to_fields = (f'{to_id}.{name}' for name in self.fk_names)
        bounds = " and ".join(
            [f'{a} = {b}' for a, b in zip(to_fields, from_fields)])
        return f"({bounds})"

    def _prep_select(self):
        if self.__is_set:
            return self.__fields, self.to_._ho_prep_select(*self.fk_names)
        return None

    @property
    def fk_names(self):
        """Returns the names of the fields composing the foreign key in the foreign table."""
        return self.__fk_names

    @fk_names.setter
    def fk_names(self, fk_names):
        """Sets the names of the fields in the foreign table."""
        self.__fk_names = fk_names

    @property
    def names(self):
        "Returns the names of the fields composing the foreign key in the table"
        return self.__fields_names

    def __repr__(self):
        """Representation of a foreign key
        """
        fields = list(self.__fields)
        fields.sort()
        fields = f"({', '.join(fields)})"
        repr_ = f"- {self.__name}: {fields}\n ↳ {normalize_fqrn(self.__fk_fqrn)}({', '.join(self.fk_names)})"
        if self.__is_set:
            repr_value = str(self.to_)
            res = []
            for line in repr_value.split('\n'):
                res.append(f'     {line}')
            res = '\n'.join(res)
            repr_ = f'{repr_}\n{res}'
        return repr_
