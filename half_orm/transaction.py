#-*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods, protected-access

"""This module provides the HoTransaction class."""

import sys

class HoTransaction:
    """The HoTransaction class is intended to be used as a class attribute of
    relation.Relation class:

    Relation.HoTransaction = HoTransaction

    The Relation.transaction can be used as a decorator of any method of a
    sub class of Relation class or any function receiving a Relation object
    as its first argument.

    Example of use:

    ```python
    gaston = halftest.relation("actor.person", first_name="Gaston")
    @gaston.HoTransaction
    def do_something(person):
        #... code to be done
    do_somethin(gaston)
    ```
    Every SQL commands executed in the do_something function will be put in a
    transaction and commited or rolled back at the end of the function.

    Functions decorated by a transaction can be nested:

    ```python
    @gaston.HoTransaction
    def second(gaston):
        # ... do something else
    @gaston.HoTransaction
    def first(gaston):
        # ... do something
        second(gaston)
    first(gaston)
    ```
    Here second is called by first and both function are played in the same
    transaction.
    """

    __level = 0
    def __init__(self, func):
        self.__func = func

    def __call__(self, relation, *args, **kwargs):
        """Each time a transaction is hit, the level is increased.
        The transaction is commited when the level is back to 0 after
        the return of the function.
        """
        res = None
        try:
            HoTransaction.__level += 1
            if relation._model._connection.autocommit:
                relation._model._connection.autocommit = False
            res = self.__func(relation, *args, **kwargs)
            HoTransaction.__level -= 1
            if HoTransaction.__level == 0:
                relation._model._connection.commit()
                relation._model._connection.autocommit = True
        except Exception as err:
            sys.stderr.write(f"HoTransaction error: {err}\nRolling back!\n")
            HoTransaction.__level = 0
            relation._model._connection.rollback()
            relation._model._connection.autocommit = True
            raise err
        return res
