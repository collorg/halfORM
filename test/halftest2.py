#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import os.path
from halfORM.model import Model

dirname = os.path.dirname(__file__)
halftest = Model('{}/halftest.ini'.format(dirname))

corto = halftest.relation("actor.person", first_name="Corto").getone()
post = halftest.relation("blog.post")
post.author_first_name = corto.first_name
post.author_last_name = corto.last_name
post.author_birth_date = corto.birth_date
post.title = 'Vaudou pour Monsieur le Président'
post.content = """Vaudou pour Monsieur le Président, qui se déroule à la Barbade (Antilles), puis sur l’île de Port-ducal (introuvable sur les cartes, mais que Pratt situe au sud-ouest de la Guadeloupe)."""
if len(post) == 0:
    post.insert()
