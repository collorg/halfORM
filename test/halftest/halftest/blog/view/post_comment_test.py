"""Test file for the halftest.blog.view.post_comment module.
"""

from halftest.base_test import BaseTest
from halftest.blog.view.post_comment import PostComment

class Test(BaseTest):

    def test_is_relation(self):
        self.assertTrue(issubclass(PostComment, self.Relation))
