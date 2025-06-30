from unittest import TestCase
import pytest
from ..init import halftest, model, HALFTEST_STR, HALFTEST_REL_LISTS
from half_orm.model import Model
from half_orm import model_errors, pg_meta

PERSON = 'actor.person'
ID_MODEL = id(model)

class Test(TestCase):
    def test_str(self):
        self.assertEqual(str(halftest.model), HALFTEST_STR)

    def test_relations_list(self):
        self.assertEqual(halftest.model._relations(), HALFTEST_REL_LISTS)

    def test_unknown_relation(self):
        "it should raise an error for unknown relations"
        with self.assertRaises(model_errors.UnknownRelation):
            model.get_relation_class("blog.unknown")

    def test_model_id_is_relation_model_id(self):
        "it should be the same model object"
        self.assertEqual(
            ID_MODEL,
            id(model.get_relation_class(PERSON)._ho_model))

    def test_get_relation_class(self):
        "it should return the same class"
        self.assertEqual(
            id(model.get_relation_class(PERSON)),
            id(model.get_relation_class(PERSON)))

    def test_get_relation_class_with_different_writings_of_qrn(self):
        "it should return the same class with different writings of qrn"
        self.assertEqual(
            id(model.get_relation_class(PERSON)),
            id(model.get_relation_class('"actor"."person"')))

    def test__import_class(self):
        "it should return the same class"
        self.assertEqual(
            id(model._import_class(PERSON)),
            id(model._import_class(PERSON)))

    def test__import_class_with_different_writings_of_qrn(self):
        "it should return the same class with different writings of qrn"
        self.assertEqual(
            id(model._import_class(PERSON)),
            id(model._import_class('"actor"."person"')))

    def test_classes(self):
        "it should return all the classes in the model"
        classes = [
            model._import_class('actor.person'),
            model._import_class('blog.post'),
            model._import_class('blog.comment'),
            model._import_class('blog.event'),
            model._import_class('blog.view.post_comment')
        ]
        for cls in model.classes():
            assert cls[0] in classes
            assert cls[1] in pg_meta.REL_CLASS_NAMES

    def test_deja_vu(self):
        "It should return an instance of the model if it's already been loaded."
        self.assertIsInstance(model._deja_vu('halftest'), Model)
        self.assertEqual(id(model._deja_vu('halftest')), ID_MODEL)

    def test_not_deja_vu(self):
        "It should return None if the model has not been seen."
        self.assertIsNone(model._deja_vu('coucou'))

    def test_register_decorator(self):
        """Test @register decorator functionality"""
        from half_orm.model import register
        
        @register
        class TestPerson(model.get_relation_class(PERSON)):
            Fkeys = {
                'comment_rfk': '_reverse_fkey_halftest_blog_comment_author_id',
                'event_rfk': '_reverse_fkey_halftest_blog_event_author_first_name_author_last_name_author_birth_date',
                'post_rfk': '_reverse_fkey_halftest_blog_post_author_first_name_author_last_name_author_birth_date',
            }
        assert TestPerson is register(TestPerson)

        with self.assertRaises(ValueError) as exc:
            @register
            class WrongClass():
                pass
        self.assertEqual("Invalid relation class: type object 'WrongClass' has no attribute '_rels_ids'", str(exc.exception))


        # check registration
        key = (model._dbname, 'actor', 'person')
        assert key in model._classes_[model._dbname]
        assert model._classes_[model._dbname][key] is TestPerson