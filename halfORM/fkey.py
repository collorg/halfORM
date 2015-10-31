"""This module provides the FKey class."""

class FKey():
    """Foreign key class
    """
    def __init__(self, fk_name, fk_sfqrn, fk_names, fields):
        self.__name = fk_name
        self.__fk_fqrn = ".".join(['"{}"'.format(elt) for elt in fk_sfqrn])
        self.__fk_names = fk_names
        self.__fields = fields
        self.__is_set = False
        self.__value = None

    def set(self, value):
        """Sets the value associated with the foreign key.

        The value must be and object of type Relation having the
        same FQRN as referenced by self.__fk_fqrn.
        """
        from halfORM.relation import Relation
        assert isinstance(value, Relation) and self.__fk_fqrn == value.fqrn
        self.__value = value
        self.__is_set = True

    @property
    def is_set(self):
        """Returns True is the foreign key is set."""
        return self.__is_set

    def __repr__(self):
        """Representation of a foreign key
        """
        fields = '({})'.format(', '.join(self.__fields))
        repr_ = "- {}: {}\n  \u21B3 {}({})".format(
            self.__name,
            fields, self.__fk_fqrn, ', '.join(self.__fk_names))
        if self.__is_set:
            repr_value = str(self.__value)
            res = []
            for line in repr_value.split('\n'):
                res.append('     {}'.format(line))
            repr_ = '{}\n{}'.format(repr_, '\n'.join(res))
        return repr_

