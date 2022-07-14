"""Test file for the halftest.blog.post module.
"""

from halftest.base_test import BaseTest
from halftest.blog.post import Post

class Test(BaseTest):

    def test_is_relation(self):
        self.assertTrue(issubclass(Post, self.Relation))

    def test_is_not_null_wrong(self):
        with self.assertRaises(AssertionError):
            self.hotAssertIsNotNull(Post, 'title')

    def test_is_not_unique(self):
        with self.assertRaises(AssertionError):
            self.hotAssertIsUnique(Post, ['title'])
        with self.assertRaises(AssertionError):
            self.hotAssertIsUnique(Post, ['content'])

    def test_title_content_is_unique(self):
        self.hotAssertIsUnique(Post, ['title', 'content'])
