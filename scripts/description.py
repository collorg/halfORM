#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys
from half_orm import model

relations = [None]
filename = sys.argv[1]
if len(sys.argv) > 2:
    relations = sys.argv[2:]
for relation in relations:
    db = model.Model(filename).desc(relation)
