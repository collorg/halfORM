# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods, protected-access

"""This module provides the Transaction class for async models."""

import sys

class AsyncTransaction:
    """
    A context manager to manage database transactions asynchronously.
    """

    __transactions = {}
    
    def __call__(self, model):
        self.__id = id(model)
        self.__transaction = None
        if self.__id not in self.__class__.__transactions:
            self.__class__.__transactions[self.__id] = {}
            self.__transaction = self.__class__.__transactions[self.__id]
            self.__transaction['level'] = 0
            self.__transaction['model'] = model
        else:
            self.__transaction = self.__transactions[self.__id]

    __init__ = __call__

    async def __aenter__(self):
        """Asynchronous version of __enter__."""
        conn = await self.__transaction['model']._connection
        if conn.autocommit:
            await conn.set_autocommit(False)
        self.__transaction['level'] += 1

    async def __aexit__(self, *_):
        """Asynchronous version of __exit__."""
        self.__transaction['level'] -= 1
        if self.__transaction['level'] == 0:
            conn = await self.__transaction['model']._connection
            try:
                # Commit asynchronously
                await conn.commit()
                # Re-enable autocommit after commit
                await conn.set_autocommit(True)
            except Exception as exc:
                # Rollback asynchronously
                await conn.rollback()

    @property
    def level(self):
        return self.__transaction.get('level')

    def is_set(self):
        return self.__transaction.get('level', 0) > 0
