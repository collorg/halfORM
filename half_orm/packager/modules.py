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

import re
import os
import sys
import importlib
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
HO_DATACLASSES = []
HO_DATACLASSES_IMPORTS = set()
INIT_MODULE_TEMPLATE = read_template('init_module_template')
MODULE_TEMPLATE_1 = read_template('module_template_1')
MODULE_TEMPLATE_2 = read_template('module_template_2')
MODULE_TEMPLATE_3 = read_template('module_template_3')
WARNING_TEMPLATE = read_template('warning')
BASE_TEST = read_template('base_test')
TEST = read_template('relation_test')

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

def __gen_dataclass(relation):
    schemaname = ''.join([elt.capitalize() for elt in relation._schemaname.split('.')])
    relationname = ''.join([elt.capitalize() for elt in relation._relationname.split('_')])
    full_class_name = f'{schemaname}{relationname}'

    rel = relation()
    dc_name = f'DC_{full_class_name}'
    fields = []
    for field_name, field in rel._ho_fields.items():
        sql_type = field._metadata['fieldtype']
        field_desc = SQL_ADAPTER.get(sql_type)
        if field_desc is None:
            field_desc = Any
            if not NO_APAPTER.get(sql_type):
                NO_APAPTER[sql_type] = 0
            NO_APAPTER[sql_type] += 1
        if field_desc.__module__ != 'builtins':
            HO_DATACLASSES_IMPORTS.add(field_desc.__module__)
            field_desc = f'{field_desc.__module__}.{field_desc.__name__}'
        else:
            field_desc = field_desc.__name__
        value = 'None'
        if field._metadata['fieldtype'][0] == '_':
            value = 'field(default_factory=list)'
        field_desc = f'{field_desc} = {value}'
        fields.append(f"\t{field_name}: {field_desc} #{sql_type}")
    datacls = [f'@dataclass\nclass {dc_name}:']
    datacls = datacls + fields
    return '\n'.join(datacls)

def __update_init_files(package_dir, files_list, warning):
    """Update __all__ lists in __init__ files.
    """
    skip = re.compile('[A-Z]')
    for root, dirs, files in os.walk(package_dir):
        if root == package_dir:
            continue
        all_ = []
        reldir = root.replace(package_dir, '')
        if re.findall(skip, reldir):
            continue
        for dir_ in dirs:
            if re.findall(skip, dir_):
                continue
        for file_ in files:
            if re.findall(skip, file_):
                continue
            path_ = os.path.join(root, file_)
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
        with open(os.path.join(root, INIT_PY), 'w', encoding='utf-8') as init_file:
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

    path[0] = package_dir
    path[1] = path[1].replace('.', os.sep)

    path = [iskeyword(elt) and f'{elt}_' or elt for elt in path]
    module_path = f"{os.path.join(*path)}.py"
    path_1 = os.path.join(*path[:-1])
    if not os.path.exists(path_1):
        os.makedirs(path_1)
    module_template = __assemble_module_template(module_path)
    inheritance_import, inherited_classes = __get_inheritance_info(
        rel, package_name)
    HO_DATACLASSES.append(__gen_dataclass(rel))
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
                class_name=camel_case(path[-1]),
                fqtn=fqtn,
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
    return module_path

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

    with open(os.path.join(package_dir, "ho_dataclasses.py"), "w", encoding='utf-8') as file_:
        file_.write(f"# dataclasses for {package_name}\n\n")
        for to_import in HO_DATACLASSES_IMPORTS:
            file_.write(f"import {to_import}\n")
        file_.write("\n")
        for dc in HO_DATACLASSES:
            file_.write(f"\n{dc}\n")

    if len(NO_APAPTER):
        print("MISSING ADAPTER FOR SQL TYPE")
        for key, value in NO_APAPTER.items():
            print(f"- {key}: {value}")
    __update_init_files(package_dir, files_list, warning)
