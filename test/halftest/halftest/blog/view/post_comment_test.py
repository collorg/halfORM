"""Test file for the halftest.blog.view.post_comment module.
"""

from halftest.base_test import BaseTest
from halftest.blog.view import post_comment
from halftest.blog.view.post_comment import PostComment
#>>> PLACE YOUR CODE BELLOW THIS LINE. DO NOT REMOVE THIS LINE!
ERR_MSG = """DeprecationWarning: halftest.blog.view.post_comment.
FKEYS variable is no longer supported!
"""

#<<< PLACE YOUR CODE ABOVE THIS LINE. DO NOT REMOVE THIS LINE!


class Test(BaseTest):
    def test_instanciate_relation(self):
        "It shoud instanciate PostComment"
        PostComment()

    def test_is_relation(self):
        "PostComment should be a subclass of half_orm.Relation."
        self.assertTrue(issubclass(PostComment, self.Relation))

    #>>> PLACE YOUR CODE BELLOW THIS LINE. DO NOT REMOVE THIS LINE!
    def test_deprecated_keys(self):
        "it should raise a DeprecationWarning error"
        post_comment.FKEYS = {}
        self.assertRaises(DeprecationWarning, PostComment)
        delattr(post_comment, 'FKEYS')
        PostComment()
