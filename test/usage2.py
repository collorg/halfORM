#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import time
from half_orm.model import Model

dpt_info = Model(config_file='/etc/half_orm/dpt_info')
oidt = dpt_info.relation(
    'collorg.core.oid_table',
    cog_oid=('e%', 'like'), cog_fqtn='seminaire.session')
for elt in oidt._ho_select('cog_oid'):
    print(elt)
print(len(oidt))
oidt._ho_update(cog_fqtn='perdu')
dpt_info.connection.commit()
print(len(oidt))
oidt2 = oidt(cog_fqtn='perdu')
for elt in oidt2:
    print(elt)
input('Allez faire un tour sur psql...')
oidt2._ho_update(cog_fqtn='seminaire.session')
dpt_info.connection.commit()
# One model shared by all the tables...
print(id(dpt_info), id(oidt.model), id(oidt2.model))
print(len(oidt2))
