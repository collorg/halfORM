"""This module provides the FKey class."""

class FKey():
    """Foreign key class

    A foreign key is set by assigning to it a Relation object of the
    corresponding type (see FKey.set method).
    It is then used to construct the join query for Relation.select
    method.
    """
    def __init__(self, fk_name, fk_sfqrn, fk_names, fields):
        self.__name = fk_name
        self.__fk_fqrn = ".".join(['"{}"'.format(elt) for elt in fk_sfqrn])
        self.__fk_names = fk_names
        self.__fields = fields
        self.__is_set = False
        self.__to = None
        self.__from = None

    def set(self, from_, to_=None):
        """Sets the value associated with the foreign key.

        The value must be and object of type Relation having the
        same FQRN as referenced by self.__fk_fqrn.
        """
        def __get_qrn(fqrn):
            """Returns QRN from FQRN."""
            return '.'.join(fqrn.split('.', 1)[1:])

        from halfORM.relation import Relation
        if to_ is None:
            to_ = from_.model.relation(__get_qrn(self.__fk_fqrn))
        if not isinstance(to_, Relation):
            raise Exception("Expecting a Relation")
        if not self.__fk_fqrn == to_.fqrn:
            raise Exception(
                "Relations must be of the same type\n{} != {}".format(
                    self.__fk_fqrn, to_.fqrn))
        self.__from = from_
        self.__to = to_
        self.__is_set = True

    @property
    def name(self):
        """Returns the name of the foreign key."""
        return self.__name

    @property
    def frel(self):
        """Returns the foreign relation associated with the fkey if any."""
        return self.__to

    @property
    def is_set(self):
        """Returns True is the foreign key is set."""
        return self.__is_set

    @property
    def fk_fqrn(self):
        """Returns the FQRN of the relation pointed to."""
        return self.__fk_fqrn

    def join_query(self, from_=None):
        """Returns the join_query, join_values of a foreign key.
        """
        if from_ is None:
            from_ = self.__from
        to_ = self.__to
        to_id = 'r{}'.format(id(to_))
        from_id = 'r{}'.format(id(from_))
        from_fields = ['{}.{}'.format(from_id, name)
                       for name in self.__fields]
        to_fields = ['{}.{}'.format(to_id, name) for name in self.__fk_names]
        bounds = ' and '.join(['{} = {}'.format(a, b) for
                               a, b in zip(to_fields, from_fields)])
        constraints_to_query = [
            '{}.{} {} %s'.format(to_id, field.name, field.comp)
            for field in to_.fields if field.is_set]
        constraints_to_values = [
            field.value for field in to_.fields if field.is_set]
        constraints_from_query = [
            '{}.{} {} %s'.format(from_id, field.name, field.comp)
            for field in from_.fields if field.is_set]
        constraints_from_values = [
            field.value for field in from_.fields if field.is_set]
        constraints_query = ' and '.join(
            constraints_to_query + constraints_from_query)
        constraints_values = constraints_to_values + constraints_from_values

        if constraints_query:
            bounds = ' and '.join([bounds, constraints_query])
        return str(bounds), constraints_values

    def __repr__(self):
        """Representation of a foreign key
        """
        fields = '({})'.format(', '.join(self.__fields))
        repr_ = "- {}: {}\n  \u21B3 {}({})".format(
            self.__name,
            fields, self.__fk_fqrn, ', '.join(self.__fk_names))
        if self.__is_set:
            repr_value = str(self.__to)
            res = []
            for line in repr_value.split('\n'):
                res.append('     {}'.format(line))
            repr_ = '{}\n{}'.format(repr_, '\n'.join(res))
        return repr_
