"""Test file for the halftest.actor.person module.
"""

from halftest.base_test import BaseTest
from halftest.actor.person import Person

class Test(BaseTest):

    def test_is_relation(self):
        self.assertTrue(issubclass(Person, self.Relation))

    def test_right_pk(self):
        "hotAssertIsPkey should pass with the right pkey"
        self.hotAssertIsPkey(Person, ('first_name', 'last_name', 'birth_date'))

    def test_wrong_pk(self):
        "hotAssertIsPkey should fail with a wrong pkey"
        with self.assertRaises(AssertionError):
            self.hotAssertIsPkey(Person, ('first_name', 'last_name'))

    def test_is_unique_ok(self):
        "hotAssertUnique should pass on 'id'"
        self.hotAssertIsUnique(Person, ['id'])

    def test_is_unique_wrong(self):
        "hotAsserUnique should fail on 'last_name'"
        with self.assertRaises(AssertionError):
            self.hotAssertIsUnique(Person, ['last_name'])

    def test_is_not_null_ok(self):
        "hotAssertIsNotNull should pass on 'id'"
        self.hotAssertIsNotNull(Person, 'id')

    def test_references_ok(self):
        "hotAssertReferences should pass"
        from halftest.blog.comment import Comment
        self.hotAssertReferences(Person, '_reverse_fkey_halftest_blog_comment_author_id', Comment)

    def test_alias_references_ok(self):
        "hotAssertAliasReferences should pass"
        from halftest.blog.comment import Comment
        self.hotAssertAliasReferences(Person, '_comment', Comment)
