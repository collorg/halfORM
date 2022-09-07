import unittest
from typing import List
from half_orm.relation import Relation

class HoTestCase(unittest.TestCase):
    def hotAssertIsPkey(self, relation: Relation, field_names: List[str]):
        "it shoud be the primary key"
        pkey = set(relation()._pkey.keys())
        if set(field_names) != pkey:
            raise self.fail(f'PKey failure: {set(field_names)} != {pkey}')

    def hotAssertIsUnique(self, relation: Relation, fields_names: List[str]):
        "Checks if a list of fields is unique for the relation."
        fields_nums = set()
        pkeynum = []
        for field_name in fields_names:
            field = relation()._fields[field_name]
            metadata = field._Field__metadata
            fields_nums.add(metadata['fieldnum'])
            if not pkeynum and metadata['pkeynum']:
                pkeynum = metadata['pkeynum']
            if not metadata['uniq'] and pkeynum != metadata['pkeynum']:
                raise self.fail(f"'{fields_names}' is not unique.")
        if fields_nums != set(pkeynum):
            raise self.fail(f"'{fields_names}' is not unique.")

    def hotAssertIsNotNull(self, relation: Relation, field_name: str):
        if not relation()._fields[field_name].is_not_null():
            raise self.fail(f"'{field_name}' is not 'not null'.")
        
    def hotAssertReferences(self, relation: Relation, fk_name: str, f_relation: Relation):
        referenced = relation()._fkeys[fk_name]()
        if not referenced._qrn == f_relation._qrn:
            raise self.fail(f"{relation}()._fkeys['{fk_name}']() does not reference {f_relation}")

    def hotAssertAliasReferences(self, relation: Relation, alias: str, f_relation: Relation):
        referenced = eval(f"relation().{alias}")
        if not referenced()._qrn == f_relation._qrn:
            raise self.fail(f"{relation}.{alias}() does not reference {f_relation}")

    def __check_update_action(self, relation: Relation, fk_name: str, update_type: str):
        return self.assertEqual(relation()._fkeys[fk_name].confupdtype, update_type)

    def __check_delete_action(self, relation: Relation, fk_name: str, delete_type: str):
        return self.assertEqual(relation()._fkeys[fk_name].confdeltype, delete_type)

    def hotAssertOnUpdateNoAction(self, relation: Relation, fk_name: str):
        return self.__check_update_action(relation, fk_name, 'a')

    def hotAssertOnUpdateRestict(self, relation: Relation, fk_name: str):
        return self.__check_update_action(relation, fk_name, 'r')

    def hotAssertOnUpdateCascade(self, relation: Relation, fk_name: str):
        return self.__check_update_action(relation, fk_name, 'c')

    def hotAssertOnUpdateSetNull(self, relation: Relation, fk_name: str):
        return self.__check_update_action(relation, fk_name, 'n')

    def hotAssertOnUpdateSetDefault(self, relation: Relation, fk_name: str):
        return self.__check_update_action(relation, fk_name, 'd')

    def hotAssertOnDeleteNoAction(self, relation: Relation, fk_name: str):
        return self.__check_delete_action(relation, fk_name, 'a')

    def hotAssertOnDeleteRestict(self, relation: Relation, fk_name: str):
        return self.__check_delete_action(relation, fk_name, 'r')

    def hotAssertOnDeleteCascade(self, relation: Relation, fk_name: str):
        return self.__check_delete_action(relation, fk_name, 'c')

    def hotAssertOnDeleteSetNull(self, relation: Relation, fk_name: str):
        return self.__check_delete_action(relation, fk_name, 'n')

    def hotAssertOnDeleteSetDefault(self, relation: Relation, fk_name: str):
        return self.__check_delete_action(relation, fk_name, 'd')

