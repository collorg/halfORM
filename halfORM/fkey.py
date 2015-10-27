class FKey():
    """Foreign key class
    """
    def __init__(self, fk_name, fk_sfqrn, fk_names, fields):
        self.__name = fk_name
        self.__fk_fqrn = ".".join(['"{}"'.format(elt) for elt in fk_sfqrn])
        self.__fk_names = fk_names
        self.__fields = fields

    def __repr__(self):
        """Representation of a foreing key
        """
        fields = '({})'.format(', '.join(self.__fields))
        return "FK {}: {}\n   \u21B3 {}({})".format(
            self.__name,
            fields, self.__fk_fqrn, ', '.join(self.__fk_names))

