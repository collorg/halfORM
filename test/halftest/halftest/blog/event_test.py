"""Test file for the halftest.blog.event module.
"""

from halftest.base_test import BaseTest
from halftest.blog.event import Event

class Test(BaseTest):

    def test_is_relation(self):
        self.assertTrue(issubclass(Event, self.Relation))
