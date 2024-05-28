from half_orm.field import Field

class NumericField(Field):
    def __init__(self, name, relation, metadata):
        self.__neg = ''
        super().__init__(name, relation, metadata)

    def __neg__(self):
        python_type = SQL_ADAPTER.get(self._sql_type)
        new = Field(self._name, self._relation, self._metadata)
        if not(python_type and isinstance(python_type(), Number)):
            raise ValueError('Not a number!')
        if self.__neg:
            new.__neg = ''
        else:
            new.__neg = '-'
        return new

    def _praf(self, query, ho_id):
        """Returns field_name prefixed with relation alias if the query is
        select. Otherwise, returns the field name quoted with ".
        """
        ho_id = f'r{ho_id}'
        if query == 'select':
            return f'{self.__neg}{ho_id}."{self._name}"'
        return f'"{self.__neg}{self._name}"'


    def _where_repr(self, query, ho_id):
        """Returns the SQL representation of the field for the where clause
        """
        where_repr = ''
        comp_str = '%s'
        comp = self._comp
        if isinstance(self._value, NumericField):
            comp_str = self._value._praf(query, ho_id)
        return f"{self._praf(query, ho_id)} {comp} {self.__neg}{comp_str}"
