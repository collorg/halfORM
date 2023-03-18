#-*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods

"""The null module provides the Null class
The Null class is used to set NULL value to relation fields.
"""

from psycopg2.extensions import register_adapter, AsIs

__all__ = ['NULL']

class Null:
    """The Null class"""

def adapt_null(_):
    """NULL adapter"""
    return AsIs("NULL")

register_adapter(Null, adapt_null)

NULL = Null()
