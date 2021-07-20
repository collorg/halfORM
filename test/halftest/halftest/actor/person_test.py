"""Test file for the halftest.actor.person module.
"""

from halftest.base_test import BaseTest
from halftest.actor.person import Person

class Test(BaseTest):

    def test_is_relation(self):
        self.assertTrue(issubclass(Person, self.Relation))
