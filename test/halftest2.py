#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import os.path
from halfORM.model import Model

dirname = os.path.dirname(__file__)
halftest = Model('{}/halftest.ini'.format(dirname))

corto = halftest.relation("actor.person", first_name="Corto").getone()
post = halftest.relation("blog.post")
post.author_first_name.value = corto.first_name.value
post.author_last_name.value = corto.last_name.value
post.author_birth_date.value = corto.birth_date.value
post.title.value = 'Vaudou pour Monsieur le Président'
post.content.value = """Vaudou pour Monsieur le Président, qui se déroule à la Barbade (Antilles), puis sur l’île de Port-ducal (introuvable sur les cartes, mais que Pratt situe au sud-ouest de la Guadeloupe)."""
if len(post) == 0:
    post.insert()
