"""Test file for the halftest.blog.comment module.
"""

from halftest.base_test import BaseTest
from halftest.blog.comment import Comment
#>>> PLACE YOUR CODE BELLOW THIS LINE. DO NOT REMOVE THIS LINE!


#<<< PLACE YOUR CODE ABOVE THIS LINE. DO NOT REMOVE THIS LINE!


class Test(BaseTest):
    def test_instanciate_relation(self):
        "It shoud instanciate Comment"
        Comment()

    def test_is_relation(self):
        "Comment should be a subclass of half_orm.Relation."
        self.assertTrue(issubclass(Comment, self.Relation))

    #>>> PLACE YOUR CODE BELLOW THIS LINE. DO NOT REMOVE THIS LINE!
