"""Test file for the halftest.blog.event module.
"""

from halftest.base_test import BaseTest
from halftest.blog.event import Event
#>>> PLACE YOUR CODE BELLOW THIS LINE. DO NOT REMOVE THIS LINE!


#<<< PLACE YOUR CODE ABOVE THIS LINE. DO NOT REMOVE THIS LINE!


class Test(BaseTest):
    def test_instanciate_relation(self):
        "It shoud instanciate Event"
        Event()

    def test_is_relation(self):
        "Event should be a subclass of half_orm.Relation."
        self.assertTrue(issubclass(Event, self.Relation))

    #>>> PLACE YOUR CODE BELLOW THIS LINE. DO NOT REMOVE THIS LINE!
