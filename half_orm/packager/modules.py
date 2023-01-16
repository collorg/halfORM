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
from keyword import iskeyword

from half_orm.pg_meta import camel_case
from half_orm.model_errors import UnknownRelation

from half_orm.packager import utils

def read_template(file_name):
    "helper"
    with open(os.path.join(utils.TEMPLATE_DIRS, file_name), encoding='utf-8') as file_:
        return file_.read()

DB_CONNECTOR_TEMPLATE = read_template('db_connector.py')
MODULE_TEMPLATE_1 = read_template('module_template_1')
MODULE_TEMPLATE_2 = read_template('module_template_2')
MODULE_TEMPLATE_3 = read_template('module_template_3')
# FKEYS_PROPS = read_template('fkeys_properties')
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
DO_NOT_REMOVE = ['db_connector.py', '__init__.py', 'base_test.py']

MODEL = None

def __update_init_files(package_dir, files_list, warning):
    """Update __all__ lists in __init__ files.
    """
    skip = re.compile('[A-Z]')
    for root, dirs, files in os.walk(package_dir):
        all_ = []
        reldir = root.replace(package_dir, '')
        if re.findall(skip, reldir):
            continue
        for dir_ in dirs:
            if re.findall(skip, dir_):
                continue
            if dir_ != '__pycache__':
                all_.append(dir_)
        for file_ in files:
            if re.findall(skip, file_):
                continue
            path_ = os.path.join(root, file_)
            if path_ not in files_list and file_ not in DO_NOT_REMOVE:
                if path_.find('__pycache__') == -1 and path_.find('_test.py') == -1:
                    print(f"REMOVING: {path_}")
                os.remove(path_)
                continue
            if (re.findall('.py$', file_) and
                    file_ != '__init__.py' and
                    file_ != '__pycache__' and
                    file_.find('_test.py') == -1):
                all_.append(file_.replace('.py', ''))
        all_.sort()
        with open(os.path.join(root, '__init__.py'), 'w', encoding='utf-8') as init_file:
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
    user_s_code = ""
    global_user_s_code = "\n"
    module_template = MODULE_FORMAT
    user_s_class_attr = ''
    if os.path.exists(module_path):
        module_code = utils.read(module_path)
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
    if not os.path.exists(module_path.replace('.py', '_test.py')):
        with open(module_path.replace('.py', '_test.py'), 'w', encoding='utf-8') as file_:
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
    repo.database.model._reload()
    if not os.path.exists(package_dir):
        os.mkdir(package_dir)
    with open(os.path.join(package_dir, 'db_connector.py'), 'w', encoding='utf-8') as file_:
        file_.write(DB_CONNECTOR_TEMPLATE.format(dbname=package_name, package_name=package_name))

    if not os.path.exists(os.path.join(package_dir, 'base_test.py')):
        with open(os.path.join(package_dir, 'base_test.py'), 'w', encoding='utf-8') as file_:
            file_.write(BASE_TEST.format(
                BEGIN_CODE=utils.BEGIN_CODE,
                END_CODE=utils.END_CODE,
                package_name=package_name))

    warning = WARNING_TEMPLATE.format(package_name=package_name)
    for relation in repo.database.model._relations():
        module_path = __update_this_module(repo, relation, package_dir, package_name)
        if module_path:
            files_list.append(module_path)
            if module_path.find('__init__.py') == -1:
                test_file_path = module_path.replace('.py', '_test.py')
                files_list.append(test_file_path)

    __update_init_files(package_dir, files_list, warning)
