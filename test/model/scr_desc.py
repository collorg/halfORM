#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys
import os.path
from halfORM import model

"""
Tests the desc method
"""
dirname = os.path.dirname(__file__)
qrn = [None]
if len(sys.argv) > 1:
    qrn = []
    for elt in sys.argv[1:]:
        qrn.append(elt)
for elt in qrn:
    db = model.Model("{}/../halftest.ini".format(dirname)).desc(elt)
