#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys
import os.path
from half_orm import model

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
    db = model.Model(f"{dirname}/../halftest.ini").desc(elt)
