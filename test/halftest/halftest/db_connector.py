#-*- coding: utf-8 -*-

"""This module exports the fonction base_relation_class which is
imported by all modules in the package halftest.
"""

from half_orm.model import Model

__all__ = ['base_relation_class']

MODEL = Model('halftest', scope=__name__)

def base_relation_class(qrn):
    """Returns the class corresponding to the QRN (qualified relation name).
    """
    cls = MODEL.get_relation_class(qrn)
    return cls
