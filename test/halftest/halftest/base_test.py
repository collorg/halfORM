"""Base test class for the halftest package.

This class is inherited by every test modules in the package.
"""

from unittest import TestCase
from half_orm.relation import Relation

class BaseTest(TestCase):

    def setUp(self) -> None:
        self.Relation = Relation

    def tearDown(self) -> None:
        pass
