#!/usr/bin/env python3

"""Batch of tests every half_orm Relation class should pass
"""

import importlib
from half_orm.model import camel_case
from half_orm import relation_errors

def set_error(err):
    """Prints the error and return True
    """
    print(err)
    return True

def check_FKEYS(module, rel):
    fkeys = module.__dict__.get('FKEYS', module.__dict__.get('FKEYS_PROPERTIES'))
    if fkeys:
        for key in fkeys:
            if not key[1] in rel._fkeys:
                raise Exception(f"FKEYS: '{key[1]}' not found in {rel.__class__.__name__}._fkeys.")

def tests(model):
    """Basic testing of each relation module in the package.
    Should instanciate each relation in the model.
    """
    error = False
    for relation in model._relations():
        fqtn = relation.split('.')[1:]
        module_name = f'.{fqtn[-1]}'
        class_name = camel_case(fqtn[-1])
        fqtn = '.'.join(fqtn[:-1])
        file_path = f'.{model.package_name}.{fqtn}'
        rel = False

        try:
            module = importlib.import_module(module_name, file_path)
            rel = module.__dict__[class_name]()
            check_FKEYS(module, rel)
        except relation_errors.DuplicateAttributeError as err:
            error = set_error(err)
        except relation_errors.IsFrozenError as err:
            error = set_error(err)
        except Exception as err:
            if rel:
                error = set_error(f'ERROR in class {rel.__class__}! {err}')
            else:
                raise err

    return not error
