#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys
from halfORM import model

filename = sys.argv[1]
db = model.Model(filename).desc()
