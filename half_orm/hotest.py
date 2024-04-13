# pylint: disable=protected-access

import unittest
from typing import List

class HoTestCase(unittest.TestCase):
    def hotAssertIsPkey(self, Rel: "Relation class", field_names: List[str]):
        "it shoud be the primary key"
        pkey = set(Rel()._ho_pkey.keys())
        if set(field_names) != pkey:
            raise self.fail(f'PKey failure: {set(field_names)} != {pkey}')

    def hotAssertIsUnique(self, Rel: "Relation class", fields_names: List[str]):
        "Checks if a list of fields is unique for the Rel."
        if (set(fields_names) == set(Rel._ho_pkey.keys())):
            return # OK it's the primary key
        for field_name in fields_names:
            field = Rel()._ho_fields[field_name]
            if not field._Field__metadata['uniq']:
                raise self.fail(f"'{fields_names}' is not unique.")

    def hotAssertIsNotNull(self, Rel: "Relation class", field_name: str):
        if not Rel()._ho_fields[field_name].is_not_null():
            raise self.fail(f"'{field_name}' is not 'not null'.")
        
    def hotAssertReferences(self, Rel: "Relation class", fk_name: str, FRelation: "Relation class"):
        referenced = Rel()._ho_fkeys[fk_name]()
        if referenced._qrn != FRelation._qrn:
            raise self.fail(f"{Rel.__class__.__name__}()._ho_fkeys['{fk_name}']() does not reference {FRelation.__name__}")

    def hotAssertAliasReferences(self, Rel: "Relation class", alias: str, FRelation: "Relation class"):
        referenced = eval(f"Rel().{alias}")
        if referenced()._qrn != FRelation._qrn:
            raise self.fail(f"{Rel.__class__.__name__}.{alias}() does not reference {FRelation.__name__}")

    def __check_update_action(self, Rel: "Relation class", fk_name: str, update_type: str):
        return self.assertEqual(Rel()._ho_fkeys[fk_name].confupdtype, update_type)

    def __check_delete_action(self, Rel: "Relation class", fk_name: str, delete_type: str):
        return self.assertEqual(Rel()._ho_fkeys[fk_name].confdeltype, delete_type)

    def hotAssertOnUpdateNoAction(self, Rel: "Relation class", fk_name: str):
        return self.__check_update_action(Rel, fk_name, 'a')

    def hotAssertOnUpdateRestict(self, Rel: "Relation class", fk_name: str):
        return self.__check_update_action(Rel, fk_name, 'r')

    def hotAssertOnUpdateCascade(self, Rel: "Relation class", fk_name: str):
        return self.__check_update_action(Rel, fk_name, 'c')

    def hotAssertOnUpdateSetNull(self, Rel: "Relation class", fk_name: str):
        return self.__check_update_action(Rel, fk_name, 'n')

    def hotAssertOnUpdateSetDefault(self, Rel: "Relation class", fk_name: str):
        return self.__check_update_action(Rel, fk_name, 'd')

    def hotAssertOnDeleteNoAction(self, Rel: "Relation class", fk_name: str):
        return self.__check_delete_action(Rel, fk_name, 'a')

    def hotAssertOnDeleteRestict(self, Rel: "Relation class", fk_name: str):
        return self.__check_delete_action(Rel, fk_name, 'r')

    def hotAssertOnDeleteCascade(self, Rel: "Relation class", fk_name: str):
        return self.__check_delete_action(Rel, fk_name, 'c')

    def hotAssertOnDeleteSetNull(self, Rel: "Relation class", fk_name: str):
        return self.__check_delete_action(Rel, fk_name, 'n')

    def hotAssertOnDeleteSetDefault(self, Rel: "Relation class", fk_name: str):
        return self.__check_delete_action(Rel, fk_name, 'd')

