#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from table import table, Model
import sys

Model('dpt_info').check()

for i in range(1000):
    table('dpt_info."collorg.core".base_table')

sys.exit()
# TODO

"""Put a constraint on a Field and iterate over the
extension.
"""
bt = table('dpt_info."collorg.core".base_table')
bt.cog_fqtn_.set('collorg.access.access')
for elt in bt:
    print(elt)
