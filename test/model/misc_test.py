from unittest import TestCase
from ..init import halftest, model, HALFTEST_STR, HALFTEST_REL_LISTS
from half_orm import model_errors

class Test(TestCase):
    def reset(self):
        pass

    def setUp(self):
        pass

    def test_str(self):
        self.assertEqual(str(halftest.model), HALFTEST_STR)

    def test_relations_list(self):
        self.assertEqual(halftest.model._relations(), HALFTEST_REL_LISTS)

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

    def test_classes(self):
        "it should return all the classes in the model"
        self.assertEqual("\n".join(
            [f"{cls[1]} {cls[0]._qrn}" for cls in model.classes()]), HALFTEST_STR)
    