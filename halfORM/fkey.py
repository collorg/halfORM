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
        from halfORM.relation import Relation
        if isinstance(value, Relation):
            assert self.__fk_fqrn == value.fqrn
        self.__value = value
        self.__is_set = True

    def __repr__(self):
        """Representation of a foreign key
        """
        fields = '({})'.format(', '.join(self.__fields))
        repr = "FK {}: {}\n   \u21B3 {}({})".format(
            self.__name,
            fields, self.__fk_fqrn, ', '.join(self.__fk_names))
        if self.__is_set:
            repr_value = str(self.__value)
            res = []
            for line in repr_value.split('\n'):
                res.append('      {}'.format(line))
            repr = '{}\n{}'.format(repr, '\n'.join(res))
        return repr

