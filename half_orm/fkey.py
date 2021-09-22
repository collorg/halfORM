#-*- coding: utf-8 -*-
# pylint: disable=protected-access

"""This module provides the FKey class."""

class FKey:
    """Foreign key class

    A foreign key is set by assigning to it a Relation object of the
    corresponding type (see FKey.set method).
    It is then used to construct the join query for Relation.select
    method.
    """
    def __init__(self, fk_name, relation, fk_sfqrn, fk_names=None, fields=None, confupdtype=None, confdeltype=None):
        self.__relation = relation
        self.__name = fk_name
        self.__is_set = False
        self.__fk_names = fk_names or []
        self.__fk_from = None
        self.__fk_to = None
        self.__confupdtype = confupdtype
        self.__confdeltype = confdeltype
        self.__fk_fqrn = ".".join(['"{}"'.format(elt) for elt in fk_sfqrn])
        self.__fields = [f'"{name}"' for name in fields]

    def __get_fk_qrn(self):
        """Returns QRN from FQRN."""
        return '.'.join(self.__fk_fqrn.split('.', 1)[1:])

    def __call__(self, __cast__=None, **kwargs):
        """Returns the relation on which the fkey is defined.
        If model._scope is set, instanciate the class from the scoped module.
        Uses the __cast if it is set.
        """
        model = self.__relation._model
        f_qrn = self.__get_fk_qrn()
        f_cast = None
        get_rel = model._import_class  if model._scope else model.get_relation_class
        if self.__name.find('_reverse_fkey_') == 0 and __cast__:
            self.__relation = get_rel(__cast__)(**self.__relation.to_dict())
        else:
            f_cast = __cast__
        f_relation = get_rel(f_cast or f_qrn)(**kwargs)
        rev_fkey_name = '_reverse_{}'.format(f_relation.id_)
        f_relation._fkeys[rev_fkey_name] = FKey(
                rev_fkey_name,
                f_relation,
                f_relation._fqrn.split('.'), self.__fields, self.__fk_names)
        f_relation._fkeys[rev_fkey_name].set(self.__relation)
        return f_relation

    def set(self, to_):
        """Sets the relation associated to the foreign key."""
        self.__set__(self.__relation, to_)

    def __set__(self, from_, to_):
        """Sets the value associated with the foreign key.

        The value must be an object of type Relation having the
        same FQRN that (or inheriting) the one referenced by self.__fk_fqrn.
        """
        from half_orm.relation import Relation

        if not issubclass(to_.__class__, Relation):
            raise Exception("Expecting a Relation")
        to_classes = set(type.mro(to_.__class__))
        self_classes = set(type.mro(self.__relation.__class__))
        common_classes = to_classes.intersection(self_classes)
        if object in common_classes:
            common_classes.remove(object)
        if not common_classes:
            raise Exception(
                "Type mismatch:\n{} != {}".format(self.__fk_fqrn, to_._fqrn))
        self.__fk_from = from_
        self.__fk_to = to_
        self.__is_set = to_.is_set()
        from_._joined_to[self] = to_

    def is_set(self):
        """Return if the foreign key is set (boolean)."""
        return self.__is_set

    def __get_to(self):
        """Returns the destination relation of the fkey."""
        return self.__fk_to
    def __set_to(self, to_):
        """Sets the destination relation of the fkey."""
        self.__fk_to = to_
    to_ = property(__get_to, __set_to)

    @property
    def fk_fqrn(self):
        """Returns the FQRN of the relation pointed to."""
        return self.__fk_fqrn

    @property
    def confupdtype(self):
        return self.__confupdtype

    @property
    def confdeltype(self):
        return self.__confdeltype

    def _join_query(self, orig_rel):
        """Returns the join_query, join_values of a foreign key.
        fkey interface: frel, from_, to_, fields, fk_names
        """
        from_ = self.__fk_from
        to_ = self.to_
        if id(from_) == id(to_):
            raise RuntimeError("You can't join a relation with itself!")
        orig_rel_id = 'r{}'.format(orig_rel.id_)
        to_id = 'r{}'.format(to_.id_)
        from_id = 'r{}'.format(from_.id_)
        if to_._qrn == orig_rel._qrn:
            to_id = orig_rel_id
        if from_._qrn == orig_rel._qrn:
            from_id = orig_rel_id
        from_fields = ('{}.{}'.format(from_id, name)
                       for name in self.__fields)
        to_fields = ('{}.{}'.format(to_id, name) for name in self.fk_names)
        bounds = " and ".join(['{} = {}'.format(a, b) for
                               a, b in zip(to_fields, from_fields)])
        return "({})".format(bounds)

    def _prep_select(self):
        if self.__is_set:
            return self.__fields, self.to_._prep_select(*self.fk_names)
        return None

    def __get_fk_names(self):
        """Returns the names of the fields in the foreign table."""
        return self.__fk_names
    def __set_fk_names(self, fk_names):
        """Sets the names of the fields in the foreign table."""
        self.__fk_names = fk_names
    fk_names = property(__get_fk_names, __set_fk_names)

    def __repr__(self):
        """Representation of a foreign key
        """
        fields = list(self.__fields)
        fields.sort()
        fields = '({})'.format(', '.join(fields))
        repr_ = u"- {}: {}\n ↳ {}({})".format(
            self.__name,
            fields, self.__fk_fqrn, ', '.join(self.fk_names))
        if self.__is_set:
            repr_value = str(self.to_)
            res = []
            for line in repr_value.split('\n'):
                res.append('     {}'.format(line))
            repr_ = '{}\n{}'.format(repr_, '\n'.join(res))
        return repr_
