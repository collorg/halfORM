from unittest import TestCase, skip
from half_orm import utils

class Test(TestCase):
    def test_check_attribute_name(self):
        "it return errors"
        self.assertEqual(utils.check_attribute_name("class"), '"class": reserved keyword in Python!')
        self.assertEqual(utils.check_attribute_name("not a valid variable"), '"not a valid variable": not a valid identifier in Python!')
