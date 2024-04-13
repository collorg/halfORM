#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

import subprocess
from unittest import TestCase

from ..init import halftest

class Test(TestCase):
    def setUp(self):
        self.pers = halftest.person_cls()

    def test_automatic_reconnection(self):
        "it should reconnect after postgresql has been restarted"
        subprocess.run(["sudo", "service", "postgresql", "restart"], check=True)
        list(self.pers())
