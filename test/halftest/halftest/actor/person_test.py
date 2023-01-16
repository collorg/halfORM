"""Test file for the halftest.actor.person module.
"""

from halftest.base_test import BaseTest
from halftest.actor.person import Person
#>>> PLACE YOUR CODE BELLOW THIS LINE. DO NOT REMOVE THIS LINE!


#<<< PLACE YOUR CODE ABOVE THIS LINE. DO NOT REMOVE THIS LINE!


class Test(BaseTest):
    def test_instanciate_relation(self):
        "It shoud instanciate Person"
        Person()

    def test_is_relation(self):
        "Person should be a subclass of half_orm.Relation."
        self.assertTrue(issubclass(Person, self.Relation))

    #>>> PLACE YOUR CODE BELLOW THIS LINE. DO NOT REMOVE THIS LINE!
