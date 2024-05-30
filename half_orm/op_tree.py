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

    @property
    def left(self):
        """Returns the left object of the set operation."""
        return self.__left

    @property
    def right(self):
        """Property returning the right operand."""
        return self.__right

    def set(self, left, operator=None, right=None):
        """
        """
        if operator:
            self.__left = left
            self.__operator = operator
        if right is not None:
            self.__right = right
