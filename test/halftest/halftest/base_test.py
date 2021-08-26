"""Base test class for the halftest package.

This class is inherited by every test modules in the package.
"""

from half_orm.relation import Relation
from half_orm import hotest

class BaseTest(hotest.HoTestCase):

    def setUp(self) -> None:
        self.Relation = Relation

    def tearDown(self) -> None:
        pass
