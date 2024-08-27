from unittest import TestCase
from ..init import halftest, model, HALFTEST_STR, HALFTEST_REL_LISTS
from half_orm import model_errors

COUCOU = 'coucou'
LE_MONDE = 'le monde'

class Test(TestCase):
    def setUp(self):
        halftest.model.execute_query('create table tbl (val integer)')
        halftest.model.reconnect(reload=True)
        self.tbl = halftest.model.get_relation_class('public.tbl')()

    def tearDown(self):
        halftest.model.execute_query('drop table tbl')
        halftest.model.reconnect(reload=True)

    def test_function_execution_with_args(self):
        res = halftest.model.execute_function('add', 1, 2)
        self.assertEqual(res, [{'add': 3}])

    def test_function_execution_with_kwargs(self):
        res = halftest.model.execute_function('concat_lower_or_upper', a=COUCOU, b=LE_MONDE, uppercase=True)
        self.assertEqual(res, [{'concat_lower_or_upper': 'COUCOU LE MONDE'}])

    def test_function_execution_error_with_mixed_arguments(self):
        with self.assertRaises(RuntimeError) as exc:
            halftest.model.execute_function('concat_lower_or_upper', COUCOU, b=LE_MONDE, uppercase=True)
        self.assertEqual(
            str(exc.exception), "You can't mix args and kwargs with the execute_function method!")

    def test_procedure_with_args(self):
        self.tbl.ho_delete(delete_all=True)
        halftest.model.call_procedure('insert_data', 10, 18)
        self.assertEqual(self.tbl().ho_count(), 2)
        self.tbl.ho_delete(delete_all=True)
        halftest.model.call_procedure('insert_data', a=11, b=19)
        self.assertEqual(self.tbl().ho_count(), 2)

    def test_procedure_call_error_with_mixed_arguments(self):
        with self.assertRaises(RuntimeError) as exc:
            halftest.model.call_procedure('insert_data', COUCOU, b=LE_MONDE)
        self.assertEqual(
            str(exc.exception), "You can't mix args and kwargs with the call_procedure method!")
