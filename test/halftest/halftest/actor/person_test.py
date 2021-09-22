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
        "hotAssertIsUnique should pass"
        self.hotAssertIsUnique(Person, 'id')

    def test_is_unique_wrong(self):
        with self.assertRaises(AssertionError):
            self.hotAssertIsUnique(Person, 'last_name')

    def test_is_not_null_ok(self):
        "hotAssertIsUnique should pass"
        self.hotAssertIsNotNull(Person, 'id')

    def test_references_ok(self):
        "hotAssertReferences should pass"
        from halftest.blog.comment import Comment
        self.hotAssertReferences(Person, '_reverse_fkey_halftest_blog_comment_author_id', Comment)

    def test_alias_references_ok(self):
        "hotAssertAliasReferences should pass"
        from halftest.blog.comment import Comment
        self.hotAssertAliasReferences(Person, '_comment', Comment)

    def test_join(self):
        "should join the objects"
        from halftest.blog.comment import Comment
        from halftest.blog.post import Post
        Post().delete(delete_all=True)
        Comment().delete(delete_all=True)
        personne = Person(**next(Person(last_name='aa').select()))
        post = Post(title='essai', content='essai')
        post.author_last_name = personne.last_name
        post.author_first_name = personne.first_name
        post.author_birth_date = personne.birth_date
        post = post.insert()[0]
        comment0 = Comment(author_id=personne.id, post_id=post['id'], content='essai').insert()[0]
        comment1 = Comment(author_id=personne.id, post_id=post['id'], content='essai 1').insert()[0]
        personne = Person(last_name='aa')
        res = personne.join(
            (Comment(), 'comments', ['id']),
            (Post(), 'posts', ['id'])
        )
        print(res)
        self.assertTrue(isinstance(res[0]['comments'], list))
        self.assertTrue(isinstance(res[0]['posts'], list))
        self.assertEqual(res[0]['posts'][0], str(post['id']))
        self.assertEqual(len(res[0]['comments']), 2)
        self.assertEqual(set(res[0]['comments']), set((str(comment0['id']), str(comment1['id']))))
        Post().delete(delete_all=True)
        Comment().delete(delete_all=True)
