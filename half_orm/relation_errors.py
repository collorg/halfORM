"""This module provides the errors for the relation module."""

class ExpectedOneError(Exception):
    """This exception is raised when get count differs from 1."""
    def __init__(self, relation, count):
        plural = '' if count == 0 else 's'
        Exception.__init__(self, 'Expected 1, got {} tuple{}:\n{}'.format(
            count, plural, relation))

class UnknownAttributeError(Exception):
    """Unknown attribute error"""
    def __init__(self, msg):
        super().__init__(
            "ERROR! Unknown attribute: {}.".format(msg))

class IsFrozenError(Exception):
    """Class is frozen"""
    def __init__(self, cls, msg):
        super().__init__(
            f"ERROR! The class {cls} is forzen.\n"
            f"Use _unfreeze to add the '{msg}' attribute to it.")

class DuplicateAttributeError(Exception):
    """Attempt to setattr to an already existing attribute."""
    def __init__(self, msg):
        super().__init__(msg)

