#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import time
from halfORM.model import Model

dpt_info = Model(config_file='/etc/halfORM/dpt_info')
oidt = dpt_info.relation(
    'collorg.core.oid_table',
    cog_oid=('e%', 'like'), cog_fqtn='seminaire.session')
for elt in oidt.select('cog_oid'):
    print(elt)
print(oidt.count())
oidt.update(cog_fqtn='perdu')
dpt_info.connection.commit()
print(oidt.count())
oidt2 = oidt(cog_fqtn='perdu')
for elt in oidt2.select():
    print(elt)
input('Allez faire un tour sur psql...')
oidt2.update(cog_fqtn='seminaire.session')
dpt_info.connection.commit()
# One model shared by all the tables...
print(id(dpt_info), id(oidt.model), id(oidt2.model))
print(oidt2.count())
