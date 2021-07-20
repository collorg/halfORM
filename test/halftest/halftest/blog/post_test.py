"""Test file for the halftest.blog.post module.
"""

from halftest.base_test import BaseTest
from halftest.blog.post import Post

class Test(BaseTest):

    def test_is_relation(self):
        self.assertTrue(issubclass(Post, self.Relation))
