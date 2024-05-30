from unittest import TestCase
from datetime import date

from half_orm.field import Field
from half_orm.null import NULL

from ..init import halftest

class Test(TestCase):
    def setUp(self):
        halftest.model.execute_query('create table if not exists test (a int, b int, c float, e text)')
        halftest.model.reconnect(reload=True)
        self.TableTest = halftest.model.get_relation_class('public.test')

    def tearDown(self):
        halftest.model.execute_query('drop table test')
        halftest.model.reconnect(reload=True)

    def test_set_same_column_equality(self):
        table = self.TableTest()
        table.a.set(table.a)
        self.assertEqual(len(table), len(self.TableTest()))

    def test_add(self):
        table = self.TableTest()
        table.b.set(table.a + 2)
        self.assertEqual(table.b._where_repr('select', '12345678'), 'r12345678."b" = (r12345678."a" + 2)')

    def test_sub(self):
        table = self.TableTest()
        table.a.set(table.b - 2)
        self.assertEqual(table.a._where_repr('select', '12345678'), 'r12345678."a" = (r12345678."b" - 2)')

    def test_mul(self):
        table = self.TableTest()
        table.b.set(table.a * 2)
        self.assertEqual(table.b._where_repr('select', '12345678'), 'r12345678."b" = (r12345678."a" * 2)')

    def test_div(self):
        # PostgreSQL doc: Division (for integral types, division truncates the result towards zero)
        table = self.TableTest()
        table.a.set(table.b / 2)
        self.assertEqual(table.a._where_repr('select', '12345678'), 'r12345678."a" = (r12345678."b" / 2)')

    def test_mod(self):
        table = self.TableTest()
        table.a.set(table.b % 2)
        self.assertEqual(table.a._where_repr('select', '12345678'), 'r12345678."a" = (r12345678."b" %% 2)')

    def test_pow(self):
        table = self.TableTest()
        table.a.set(table.b ** 2)
        self.assertEqual(table.a._where_repr('select', '12345678'), 'r12345678."a" = (r12345678."b" ^ 2)')

    def test_abs(self):
        table = self.TableTest()
        table.a.set(abs(table.b))
        self.assertEqual(table.a._where_repr('select', '12345678'), 'r12345678."a" = abs(r12345678."b")')


    def test_floor(self):
        table = self.TableTest()
        table.a.set(table.c.__floor__())
        self.assertEqual(table.a._where_repr('select', '12345678'), 'r12345678."a" = floor(r12345678."c")')

    def test_neg(self):
        table = self.TableTest()
        table.a.set(-table.a)
        self.assertEqual(table.a._where_repr('select', '12345678'), 'r12345678."a" = -r12345678."a"')
        table = self.TableTest()
        table.a.set(--table.a)
        self.assertEqual(table.a._where_repr('select', '12345678'), 'r12345678."a" = r12345678."a"')

    def test_error(self):
        table = self.TableTest()
        with self.assertRaises(TypeError) as exc:
            table.a.set(table.c + 'a')
        with self.assertRaises(TypeError) as exc:
            table.a.set(table.c - 'a')
        with self.assertRaises(TypeError) as exc:
            table.a.set(table.c * 'a')
        with self.assertRaises(TypeError) as exc:
            table.a.set(table.c / 'a')
        with self.assertRaises(TypeError) as exc:
            table.a.set(table.c % 'a')
        with self.assertRaises(TypeError) as exc:
            table.a.set(table.c ** 'a')

    def test_right_numfield(self):
        table = self.TableTest()
        table.a.set(table.b * table.c)
        self.assertEqual(table.a._where_repr('select', '12345678'), 'r12345678."a" = (r12345678."b" * r12345678."c")')
