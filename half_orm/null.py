# -*- coding: utf-8 -*-
# pylint: disable=too-few-public-methods

"""The null module provides the Null class
The Null class is used to set NULL value to relation fields.
"""

import psycopg

__all__ = ['NULL']

class Null:
    """The Null singleton class"""
    pass

NULL = Null()
