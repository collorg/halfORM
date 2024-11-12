#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# pylint: disable=invalid-name, protected-access

"""
Generates/Patches/Synchronizes a hop Python package with a PostgreSQL database
with the `hop` command.

Initiate a new project and repository with the `hop create <project_name>` command.
The <project_name> directory should not exist when using this command.

In the dbname directory generated, the hop command helps you patch, test and
deal with CI.

TODO:
On the 'devel' or any private branch hop applies patches if any, runs tests.
On the 'main' or 'master' branch, hop checks that your git repo is in sync with
the remote origin, synchronizes with devel branch if needed and tags your git
history with the last release applied.
"""

import importlib
import os
import re
import sys
import time
from keyword import iskeyword
from typing import Any

from half_orm.pg_meta import camel_case
from half_orm.model_errors import UnknownRelation
from half_orm.sql_adapter import SQL_ADAPTER

from half_orm import utils

def read_template(file_name):
    "helper"
    with open(os.path.join(utils.TEMPLATE_DIRS, file_name), encoding='utf-8') as file_:
        return file_.read()

NO_APAPTER = {}
HO_DATACLASSES = [
'''from dataclasses import dataclass, field
from half_orm.relation import DC_Relation
from half_orm.field import Field''']
HO_DATACLASSES_IMPORTS = set()
INIT_MODULE_TEMPLATE = read_template('init_module_template')
MODULE_TEMPLATE_1 = read_template('module_template_1')
MODULE_TEMPLATE_2 = read_template('module_template_2')
MODULE_TEMPLATE_3 = read_template('module_template_3')
WARNING_TEMPLATE = read_template('warning')
BASE_TEST = read_template('base_test')
TEST = read_template('relation_test')
SKIP = re.compile('[A-Z]')

MODULE_FORMAT = (
    "{rt1}" +
    "{bc_}{global_user_s_code}{ec_}" +
    "{rt2}" +
    "    {bc_}{user_s_class_attr}    {ec_}" +
    "{rt3}\n        " +
    "{bc_}{user_s_code}")
AP_EPILOG = """"""
INIT_PY = '__init__.py'
BASE_TEST_PY = 'base_test.py'
DO_NOT_REMOVE = [INIT_PY, BASE_TEST_PY]
TEST_EXT = '_test.py'

MODEL = None

def __get_full_class_name(schemaname, relationname):
    schemaname = ''.join([elt.capitalize() for elt in schemaname.split('.')])
    relationname = ''.join([elt.capitalize() for elt in relationname.split('_')])
    return f'{schemaname}{relationname}'

def __get_field_desc(field_name, field):
    #TODO: REFACTOR
    sql_type = field._metadata['fieldtype']
    field_desc = SQL_ADAPTER.get(sql_type)
    if field_desc is None:
        if not NO_APAPTER.get(sql_type):
            NO_APAPTER[sql_type] = 0
        NO_APAPTER[sql_type] += 1
        field_desc = Any
    if field_desc.__module__ != 'builtins':
        HO_DATACLASSES_IMPORTS.add(field_desc.__module__)
        field_desc = f'{field_desc.__module__}.{field_desc.__name__}'
    else:
        field_desc = field_desc.__name__
    value = 'field(default=None)'
    if field._metadata['fieldtype'][0] == '_':
        value = 'field(default_factory=list)'
    field_desc = f'{field_desc} = {value}'
    field_desc = f"    {field_name}: {field_desc}"
    error = utils.check_attribute_name(field_name)
    if error:
        field_desc = f'# {field_desc} FIX ME! {error}'
    return field_desc

def __gen_dataclass(relation, fkeys):
    rel = relation()
    dc_name = f'DC_{__get_full_class_name(relation._schemaname, relation._relationname)}'
    fields = []
    post_init = ['    def __post_init__(self):']
    for field_name, field in rel._ho_fields.items():
        fields.append(__get_field_desc(field_name, field))
        post_init.append(f'        self.{field_name}: Field = None')

    fkeys = {value:key for key, value in fkeys.items() if key != ''}
    for key, value in rel()._ho_fkeys.items():
        if key in fkeys:
            fkey_alias = fkeys[key]
            fdc_name = f'DC_{__get_full_class_name(*(value._FKey__fk_fqrn[1:]))}'
            post_init.append(f"        self.{fkey_alias} = {fdc_name}")
    return '\n'.join([f'@dataclass\nclass {dc_name}(DC_Relation):'] + fields + post_init)

def __get_modules_list(dir, files_list, files):
    all_ = []
    for file_ in files:
        if re.findall(SKIP, file_):
            continue
        path_ = os.path.join(dir, file_)
        if path_ not in files_list and file_ not in DO_NOT_REMOVE:
            if path_.find('__pycache__') == -1 and path_.find(TEST_EXT) == -1:
                print(f"REMOVING: {path_}")
            os.remove(path_)
            continue
        if (re.findall('.py$', file_) and
                file_ != INIT_PY and
                file_ != '__pycache__' and
                file_.find(TEST_EXT) == -1):
            all_.append(file_.replace('.py', ''))
    all_.sort()
    return all_

def __update_init_files(package_dir, files_list, warning):
    """Update __all__ lists in __init__ files.
    """
    for dir, _, files in os.walk(package_dir):
        if dir == package_dir:
            continue
        reldir = dir.replace(package_dir, '')
        if re.findall(SKIP, reldir):
            continue
        all_ = __get_modules_list(dir, files_list, files)
        with open(os.path.join(dir, INIT_PY), 'w', encoding='utf-8') as init_file:
            init_file.write(f'"""{warning}"""\n\n')

            all_ = ",\n    ".join([f"'{elt}'" for elt in all_])
            init_file.write(f'__all__ = [\n    {all_}\n]\n')

def __get_inheritance_info(rel, package_name):
    """Returns inheritance informations for the rel relation.
    """
    inheritance_import_list = []
    inherited_classes_aliases_list = []
    for base in rel.__class__.__bases__:
        if base.__name__ != 'Relation':
            inh_sfqrn = list(base._t_fqrn)
            inh_sfqrn[0] = package_name
            inh_cl_alias = f"{camel_case(inh_sfqrn[1])}{camel_case(inh_sfqrn[2])}"
            inh_cl_name = f"{camel_case(inh_sfqrn[2])}"
            from_import = f"from {'.'.join(inh_sfqrn)} import {inh_cl_name} as {inh_cl_alias}"
            inheritance_import_list.append(from_import)
            inherited_classes_aliases_list.append(inh_cl_alias)
    inheritance_import = "\n".join(inheritance_import_list)
    inherited_classes = ", ".join(inherited_classes_aliases_list)
    if inherited_classes.strip():
        inherited_classes = f"{inherited_classes}, "
    return inheritance_import, inherited_classes

def __get_fkeys(repo, class_name, module_path):
    try:
        mod_path = module_path.replace(repo.base_dir, '').replace(os.path.sep, '.')[1:-3]
        mod = importlib.import_module(mod_path)
        importlib.reload(mod)
        cls = mod.__dict__[class_name]
        fkeys = cls.__dict__.get('Fkeys', {})
        return fkeys
    except ModuleNotFoundError:
        pass
    return {}

def __assemble_module_template(module_path):
    """Construct the module after slicing it if it already exists.
    """
    ALT_BEGIN_CODE = "#>>> PLACE YOUR CODE BELLOW THIS LINE. DO NOT REMOVE THIS LINE!\n"
    user_s_code = ""
    global_user_s_code = "\n"
    module_template = MODULE_FORMAT
    user_s_class_attr = ''
    if os.path.exists(module_path):
        module_code = utils.read(module_path)
        if module_code.find(ALT_BEGIN_CODE) != -1:
            module_code = module_code.replace(ALT_BEGIN_CODE, utils.BEGIN_CODE)
        user_s_code = module_code.rsplit(utils.BEGIN_CODE, 1)[1]
        user_s_code = user_s_code.replace('{', '{{').replace('}', '}}')
        global_user_s_code = module_code.rsplit(utils.END_CODE)[0].split(utils.BEGIN_CODE)[1]
        global_user_s_code = global_user_s_code.replace('{', '{{').replace('}', '}}')
        user_s_class_attr = module_code.split(utils.BEGIN_CODE)[2].split(f'    {utils.END_CODE}')[0]
        user_s_class_attr = user_s_class_attr.replace('{', '{{').replace('}', '}}')
    return module_template.format(
        rt1=MODULE_TEMPLATE_1, rt2=MODULE_TEMPLATE_2, rt3=MODULE_TEMPLATE_3,
        bc_=utils.BEGIN_CODE, ec_=utils.END_CODE,
        global_user_s_code=global_user_s_code,
        user_s_class_attr=user_s_class_attr,
        user_s_code=user_s_code)

def __update_this_module(
        repo, relation, package_dir, package_name):
    """Updates the module."""
    _, fqtn = relation
    path = list(fqtn)
    if path[1].find('half_orm_meta') == 0:
        # hop internal. do nothing
        return None
    fqtn = '.'.join(path[1:])
    try:
        rel = repo.database.model.get_relation_class(fqtn)()
    except (TypeError, UnknownRelation) as err:
        sys.stderr.write(f"{err}\n{fqtn}\n")
        sys.stderr.flush()
        return None
    fields = []
    kwargs = []
    arg_names = []
    for key, value in rel._ho_fields.items():
        error = utils.check_attribute_name(key)
        if not error:
            fields.append(f"self.{key}: Field = None")
            kwargs.append(f"{key}: '{str(value.py_type.__name__)}'=None")
            arg_names.append(f'{key}={key}')
    fields = "\n        ".join(fields)
    kwargs = ", ".join(kwargs)
    arg_names = ", ".join(arg_names)
    path[0] = package_dir
    path[1] = path[1].replace('.', os.sep)

    path = [iskeyword(elt) and f'{elt}_' or elt for elt in path]
    class_name = camel_case(path[-1])
    module_path = f"{os.path.join(*path)}.py"
    path_1 = os.path.join(*path[:-1])
    if not os.path.exists(path_1):
        os.makedirs(path_1)
    module_template = __assemble_module_template(module_path)
    inheritance_import, inherited_classes = __get_inheritance_info(
        rel, package_name)
    with open(module_path, 'w', encoding='utf-8') as file_:
        documentation = "\n".join([line and f"    {line}" or "" for line in str(rel).split("\n")])
        file_.write(
            module_template.format(
                hop_release = utils.hop_version(),
                module=f"{package_name}.{fqtn}",
                package_name=package_name,
                documentation=documentation,
                inheritance_import=inheritance_import,
                inherited_classes=inherited_classes,
                class_name=class_name,
                dc_name=f'DC_{__get_full_class_name(rel._schemaname, rel._relationname)}',
                fqtn=fqtn,
                kwargs=kwargs,
                arg_names=arg_names,
                warning=WARNING_TEMPLATE.format(package_name=package_name)))
    if not os.path.exists(module_path.replace('.py', TEST_EXT)):
        with open(module_path.replace('.py', TEST_EXT), 'w', encoding='utf-8') as file_:
            file_.write(TEST.format(
                BEGIN_CODE=utils.BEGIN_CODE,
                END_CODE=utils.END_CODE,
                package_name=package_name,
                module=f"{package_name}.{fqtn}",
                class_name=camel_case(path[-1]))
            )
    HO_DATACLASSES.append(__gen_dataclass(
        rel, __get_fkeys(repo, class_name, module_path)))
    return module_path

def __reset_dataclasses(repo, package_dir):
    with open(os.path.join(package_dir, "ho_dataclasses.py"), "w", encoding='utf-8') as file_:
        for relation in repo.database.model._relations():
            t_qrn = relation[1][1:]
            if t_qrn[0].find('half_orm') == 0:
                continue
            file_.write(f'class DC_{__get_full_class_name(*t_qrn)}: ...\n')

def __gen_dataclasses(package_dir, package_name):
    with open(os.path.join(package_dir, "ho_dataclasses.py"), "w", encoding='utf-8') as file_:
        file_.write(f"# dataclasses for {package_name}\n\n")
        hd_imports = list(HO_DATACLASSES_IMPORTS)
        hd_imports.sort()
        for to_import in hd_imports:
            file_.write(f"import {to_import}\n")
        file_.write("\n")
        for dc in HO_DATACLASSES:
            file_.write(f"\n{dc}\n")

def generate(repo):
    """Synchronize the modules with the structure of the relation in PG.
    """
    package_name = repo.name
    package_dir = os.path.join(repo.base_dir, package_name)
    files_list = []
    try:
        sql_adapter_module = importlib.import_module('sql_adapter', package_dir)
        SQL_ADAPTER.update(sql_adapter_module.SQL_ADAPTER)
    except ModuleNotFoundError as exc:
        sys.stderr.write(f"{exc}\n")
    except AttributeError as exc:
        sys.stderr.write(f"{exc}\n")
    repo.database.model._reload()
    if not os.path.exists(package_dir):
        os.mkdir(package_dir)

    __reset_dataclasses(repo, package_dir)

    with open(os.path.join(package_dir, INIT_PY), 'w', encoding='utf-8') as file_:
        file_.write(INIT_MODULE_TEMPLATE.format(package_name=package_name))

    if not os.path.exists(os.path.join(package_dir, BASE_TEST_PY)):
        with open(os.path.join(package_dir, BASE_TEST_PY), 'w', encoding='utf-8') as file_:
            file_.write(BASE_TEST.format(
                BEGIN_CODE=utils.BEGIN_CODE,
                END_CODE=utils.END_CODE,
                package_name=package_name))
    warning = WARNING_TEMPLATE.format(package_name=package_name)
    for relation in repo.database.model._relations():
        module_path = __update_this_module(repo, relation, package_dir, package_name)
        if module_path:
            files_list.append(module_path)
            if module_path.find(INIT_PY) == -1:
                test_file_path = module_path.replace('.py', TEST_EXT)
                files_list.append(test_file_path)

    __gen_dataclasses(package_dir, package_name)

    if len(NO_APAPTER):
        print("MISSING ADAPTER FOR SQL TYPE")
        for key, value in NO_APAPTER.items():
            print(f"- {key}: {value}")
    __update_init_files(package_dir, files_list, warning)
