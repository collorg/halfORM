#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import sys
from halfORM import model

db = model.Model(sys.argv[1]).desc()
