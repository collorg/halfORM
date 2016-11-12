#-*- coding: utf-8 -*-

__all__ = ['base_relation_class']

from half_orm.model import Model

__model = Model('{dbname}', scope=__name__)

def base_relation_class(fqrn):
    cls = __model.get_relation_class(fqrn)
    return cls
