class OpTree:
    """OpTree stores in a tree structure operators and operands.
    """
    def __init__(self, left, operator=None, right=None):
        self.__left = left
        self.__operator = operator
        self.__right = right

    @property
    def operator(self):
        """Property returning the __operator value."""
        return self.__operator
    @operator.setter
    def operator(self, operator):
        """Set operator setter."""
        self.__operator = operator

    @property
    def left(self):
        """Returns the left object of the set operation."""
        return self.__left
    @left.setter
    def left(self, left):
        """left operand setter."""
        self.__left = left

    @property
    def right(self):
        """Property returning the right operand."""
        return self.__right
    @right.setter
    def right(self, right):
        """right operand setter."""
        self.__right = right

    def set(self, left, operator=None, right=None):
        """
        """
        if operator:
            self.__left = left
            self.__operator = operator
        if right is not None:
            self.__right = right
