import numbers
from half_orm.field import Field


class NumericField(Field):
    def __init__(self, name, relation, metadata):
        super().__init__(name, relation, metadata)
        self.__neg = ''
        self.__abs = ''
        self.__floor = ''
        self.__operands = set()

    def __neg__(self):
        if self.__neg == '-':
            self.__neg = ''
        else:
            self.__neg = '-'
        return self

    def _praf(self, query, ho_id, left=False):
        """Returns field_name prefixed with relation alias if the query is
        select. Otherwise, returns the field name quoted with ".
        """
        praf = f'"{self._name}"'
        if query == 'select':
            praf = f'r{ho_id}."{self._name}"'
        if not left:
            for operand in self.__operands:
                right = operand[1]
                if isinstance(right, NumericField):
                    right = right._praf(query, ho_id)
                praf = f'({praf} {operand[0]} {right})'
            if self.__abs:
                praf = f'abs({praf})'
            if self.__floor:
                praf = f'floor({praf})'
        return praf

    def _where_repr(self, query, ho_id):
        """Returns the SQL representation of the field for the where clause
        """
        where_repr = ''
        comp_str = '%s'
        comp = self._comp
        if isinstance(self._value, NumericField):
            comp_str = self._value._praf(query, ho_id)
        return f"{self._praf(query, ho_id, True)} {comp} {self.__neg}{comp_str}"

    def __add__(self, other):
        if isinstance(other, numbers.Number) or isinstance(other, NumericField):
            self.__operands.add(('+', other))
            return self
        else:
            raise TypeError('Unsupported operand type for +: a Number was expected.')

    def __sub__(self, other):
        if isinstance(other, numbers.Number) or isinstance(other, NumericField):
            self.__operands.add(('-', other))
            return self
        else:
            raise TypeError('Unsupported operand type for -: a Number was expected.')

    def __mul__(self, other):
        if isinstance(other, numbers.Number) or isinstance(other, NumericField):
            self.__operands.add(('*', other))
            return self
        else:
            raise TypeError('Unsupported operand type for *: a Number was expected.')

    def __truediv__(self, other):
        if isinstance(other, numbers.Number) or isinstance(other, NumericField):
            self.__operands.add(('/', other))
            return self
        else:
            raise TypeError('Unsupported operand type for /: a Number was expected.')

    def __mod__(self, other):
        if isinstance(other, numbers.Number) or isinstance(other, NumericField):
            self.__operands.add(('%%', other))
            return self
        else:
            raise TypeError('Unsupported operand type for %: a Number was expected.')

    def __pow__(self, other):
        if isinstance(other, numbers.Number) or isinstance(other, NumericField):
            self.__operands.add(('^', other))
            return self
        else:
            raise TypeError('Unsupported operand type for **: a Number was expected.')
        return self

    def __abs__(self):
        self.__abs = 'abs'
        return self

    def __floor__(self):
        self.__floor = 'floor'
        return self
