"""This module provides the Field class."""

class Field():
    """The class Field is for Relation internal usage. It is called by
    the RelationFactory metaclass for each field in the relation considered.
    """
    __slots__ = [
        '__name', '__metadata', '__is_set', '__value', '__comp'
    ]
    def __init__(self, name, metadata):
        self.__name = name
        self.__metadata = metadata
        self.__is_set = False
        self.__value = None
        self.__comp = '='

    def __repr__(self):
        md_ = self.__metadata
        repr_ = "({}) {}".format(
            md_['fieldtype'], md_['pkey'] and 'PK' or ('{}{}'.format(
                md_['uniq'] and 'UNIQUE ' or '',
                md_['notnull'] and 'NOT NULL' or '')))
        if self.__is_set:
            repr_ = "{} ({} {} {})".format(
                repr_, self.__name, self.__comp, self.__value)
        return repr_

    def __str__(self):
        return str(self.value)

    @property
    def name(self):
        """This property returns the name of the field."""
        return self.__name

    @property
    def is_set(self):
        "This property returns a boolean indicating if the field is set of not."
        return self.__is_set

    def get(self):
        "Returns the value of the field object"
        return self.__value

    def set(self, value, comp=None):
        """Sets the value (and the comparator) associated with the field."""
        if isinstance(value, tuple):
            assert len(value) == 2
            value, comp = value
        if value is None and comp is None:
            comp = 'is'
        if value is None:
            assert comp == 'is' or comp == 'is not'
        elif comp is None:
            comp = '='
        self.__is_set = True
        self.__value = value
        self.__comp = comp

    value = property(get, set)

    @property
    def comp(self):
        "This property returns the comparator associated with the value."
        return self.__comp
