#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

import sys
from unittest import TestCase
from datetime import date

from ..init import halftest
from halfORM import relation_errors, model

class Test(TestCase):
    def tearDown(self):
        self.pers().delete(nom=('%', 'like'))

    def setUp(self):
        self.pers = halftest.relation("public.personne")
        self.billet = halftest.relation("public.billet")

    def insertion_test(self):
        """Insertion test"""
        pers = self.pers
        pers.model.connection.autocommit = False
        for i in range(26):
            for j in range(10):
                nom = 'n{}{}'.format(chr(ord('a') + i), j)
                prenom = 'p{}{}'.format(i, j)
                date_naiss = date.today()
                self.pers.insert(nom=nom, prenom=prenom, date_naiss=date_naiss)
        pers.model.connection.commit()
        pers.model.connection.autocommit = True
        self.assertEqual(pers().count(), 260)

    def __update_test(self):
        pers = self.pers()
        count = pers.nom.set('a%', 'like')
        pers.nom.set('a%', 'like')
        self.assertEqual(pers.count(), 10)
        pers.update(nom=pers.nom.uppercase())
        self.assertEqual(pers.count(), 0)
        self.assertEqual(pers.count(nom=('A%', 'like')), 10)

