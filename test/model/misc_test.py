from unittest import TestCase
from ..init import halftest, model
from half_orm import model_errors

class Test(TestCase):
    def reset(self):
        pass

    def setUp(self):
        pass

    def test_unknown_relation(self):
        "it should raise an error for unknown relations"
        with self.assertRaises(model_errors.UnknownRelation):
            model.get_relation_class("blog.unknown")

    def test_get_relation_class(self):
        "it should return the same class"
        self.assertEqual(
            id(model.get_relation_class('actor.person')),
            id(model.get_relation_class('actor.person')))

    def test_get_relation_class_with_different_writings_of_qrn(self):
        "it should return the same class with different writings of qrn"
        self.assertEqual(
            id(model.get_relation_class('actor.person')),
            id(model.get_relation_class('"actor"."person"')))

    def test__import_class(self):
        "it should return the same class"
        self.assertEqual(
            id(model._import_class('actor.person')),
            id(model._import_class('actor.person')))

    def test__import_class_with_different_writings_of_qrn(self):
        "it should return the same class with different writings of qrn"
        self.assertEqual(
            id(model._import_class('actor.person')),
            id(model._import_class('"actor"."person"')))
