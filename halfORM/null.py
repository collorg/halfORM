#-*- coding: utf-8 -*-

"""The null module provides the Null class
The Null class is used to set NULL value to relation fields.
"""

__all__ = ['NULL']

from psycopg2.extensions import register_adapter, AsIs

class Null:
    """The Null class"""
    pass

def adapt_null(_):
    return AsIs("NULL")

register_adapter(Null, adapt_null)

NULL = Null()
