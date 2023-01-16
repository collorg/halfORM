"""Test file for the halftest.blog.post module.
"""

from halftest.base_test import BaseTest
from halftest.blog.post import Post
#>>> PLACE YOUR CODE BELLOW THIS LINE. DO NOT REMOVE THIS LINE!


#<<< PLACE YOUR CODE ABOVE THIS LINE. DO NOT REMOVE THIS LINE!


class Test(BaseTest):
    def test_instanciate_relation(self):
        "It shoud instanciate Post"
        Post()

    def test_is_relation(self):
        "Post should be a subclass of half_orm.Relation."
        self.assertTrue(issubclass(Post, self.Relation))

    #>>> PLACE YOUR CODE BELLOW THIS LINE. DO NOT REMOVE THIS LINE!
