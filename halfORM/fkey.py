class FKey():
    """Foreign key class
    """
    def __init__(self, fk_name, fk_sfqrn, fk_names, fields):
        self.__name = fk_name
        self.__fk_fqrn = ".".join(['"{}"'.format(elt) for elt in fk_sfqrn])
        self.__fk_names = fk_names
        self.__fields = fields
        self.__is_set = False
        self.__foreign = None

    def set(self, value):
        if value.isinstance(Relation):
            assert self.__fk_fqrn == relation.fqrn
        self.__foreign = value
        self.__is_set = True

    def __repr__(self):
        """Representation of a foreign key
        """
        fields = '({})'.format(', '.join(self.__fields))
        return "FK {}: {}\n   \u21B3 {}({})".format(
            self.__name,
            fields, self.__fk_fqrn, ', '.join(self.__fk_names))

