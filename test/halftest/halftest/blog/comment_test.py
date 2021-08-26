"""Test file for the halftest.blog.comment module.
"""

from halftest.base_test import BaseTest
from halftest.blog.comment import Comment

class Test(BaseTest):

    def test_is_relation(self):
        self.assertTrue(issubclass(Comment, self.Relation))

    def test_fk_author_deltype(self):
        self.hotAssertOnDeleteCascade(Comment, 'author')