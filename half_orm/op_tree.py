class OpTree:
    """OpTree stores in a tree structure operators and operands.
    """
    def __init__(self, left):
        self.__left = left
        self.__operator = None
        self.__right = None

    @property
    def operator(self):
        """Property returning the __operator value."""
        return self.__operator

    @property
    def left(self):
        """Returns the left operand."""
        return self.__left

    @property
    def right(self):
        """Returns the right operand."""
        return self.__right

    def set(self, left, operator=None, right=None):
        """
        """
        self.__left = left
        self.__operator = operator
        self.__right = right
        return self
