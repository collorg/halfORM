#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# pylint: disable=invalid-name, protected-access

"""\
Generates a python package from a PostgreSQL database
"""

import re
import os
import sys
from keyword import iskeyword

from half_orm.model import Model, camel_case

HALFORM_PATH = os.path.dirname(__file__)

BEGIN_CODE = "#>>> Place your code bellow\n"
END_CODE = "#<<< Place your code above\n"
BEGIN_CODE_I = "#>>>\xa0Place your code bellow"
END_CODE_I = "#<<<\xa0Place your code above"

README = open('{}/halfORM_templates/README'.format(HALFORM_PATH)).read()

CONFIG_TEMPLATE = open(
    '{}/halfORM_templates/config'.format(HALFORM_PATH)).read()

SETUP_TEMPLATE = open(
    '{}/halfORM_templates/setup.py'.format(HALFORM_PATH)).read()

DB_CONNECTOR_TEMPLATE = open(
    '{}/halfORM_templates/db_connector.py'.format(HALFORM_PATH)).read()

MODULE_TEMPLATE_1 = open(
    '{}/halfORM_templates/module_template_1'.format(HALFORM_PATH)
    ).read().format(bc_i=BEGIN_CODE_I, ec_i=END_CODE_I)

MODULE_TEMPLATE_2 = open(
    '{}/halfORM_templates/module_template_2'.format(HALFORM_PATH)).read()

MODULE_TEMPLATE_3 = open(
    '{}/halfORM_templates/module_template_3'.format(HALFORM_PATH)).read()

MODULE_TEMPLATE_4 = open(
    '{}/halfORM_templates/module_template_4'.format(HALFORM_PATH)).read()

MODULE_FORMAT_1 = (
    "{rt1}{bc}{c1_}{ec}"
    "{rt2}    {bc}{c2_}    {ec}"
    "{rt3}        {bc}{c3_}        {ec}"
    "{rt4}        {bc}{c4_}        {ec}\n"
    "    {bc}{c5_}")
MODULE_FORMAT_2 = (
    "{rt1}{bc}{c1_}{ec}"
    "{rt2}    {bc}{c2_}{ec}"
    "{rt3}        {bc}{c3_}{ec}"
    "{rt4}        {bc}{c4_}{ec}\n"
    "    {bc}{c5_}")

AP_DESCRIPTION = """Generates python package from a PG database"""
AP_EPILOG = """"""

DO_NOT_REMOVE = ['db_connector.py', '__init__.py']

def load_config_file(base_dir=None, ref_dir=None):
    """Try to retrieve halfORM configuration file of the package.
    This method is called when no half_orm config file is provided.
    It changes to the package base directory if the config file exists.
    """
    import configparser
    config = configparser.ConfigParser()

    if not base_dir:
        ref_dir = os.path.abspath(os.path.curdir)
        base_dir = ref_dir
    if os.path.exists('.halfORM/config'):
        config.read('.halfORM/config')
        config_file = config['halfORM']['config_file']
        package_name = config['halfORM']['package_name']
        return (config_file, package_name)
    if os.path.abspath(os.path.curdir) != '/':
        os.chdir('..')
        cur_dir = os.path.abspath(os.path.curdir)
        return load_config_file(cur_dir, ref_dir)
    # restore reference directory.
    os.chdir(ref_dir)
    return None, None

def init_package(model, package_dir, package_name):
    """Initialize different files in the package directory.
    """
    dbname = model._dbname
    if not os.path.exists(package_name):
        os.makedirs(package_dir)
        setup = SETUP_TEMPLATE.format(dbname=dbname, package_name=package_name)
        setup_file_name = '{}/setup.py'.format(package_name)
        if not os.path.exists(setup_file_name):
            open(setup_file_name, 'w').write(setup)
    open('{}/db_connector.py'.format(package_dir), 'w').write(
        DB_CONNECTOR_TEMPLATE.format(dbname=dbname, package_name=package_name))
    os.makedirs('{}/.halfORM'.format(package_name))
    open('{}/.halfORM/config'.format(package_name), 'w').write(
        CONFIG_TEMPLATE.format(
            config_file=model._dbname, package_name=package_name))
    readme_file_name = '{}/README.rst'.format(package_name)
    cmd = " ".join(sys.argv)
    readme = README.format(cmd=cmd, dbname=dbname, package_name=package_name)
    open(readme_file_name, 'w').write(readme)

def get_inheritance_info(rel, package_name):
    """Returns inheritance informations for the rel relation.
    """
    inheritance_import_list = []
    inherited_classes_list = []
    for base in rel.__class__.__bases__:
        if base.__name__ != 'Relation':
            inh_sfqrn = list(base.__sfqrn)
            inh_sfqrn[0] = package_name
            inh_cl_name = camel_case(inh_sfqrn[-1])
            inheritance_import_list.append(
                "from {} import {}".format(".".join(inh_sfqrn), inh_cl_name)
            )
            inherited_classes_list.append(inh_cl_name)
    inheritance_import = "\n".join(inheritance_import_list)
    inherited_classes = ", ".join(inherited_classes_list)
    return inheritance_import, inherited_classes

def make_module(module_path):
    """Construct the module after slicing it if it already exists.
    """
    c1_ = ""
    c2_ = ""
    c3_ = ""
    c4_ = ""
    c5_ = ""
    module_template = MODULE_FORMAT_1
    if os.path.exists(module_path):
        module_template = MODULE_FORMAT_2
        slices = [elt.split(END_CODE)
                  for elt in open(module_path).read().split(BEGIN_CODE)]
        c1_ = slices[1][0]
        c2_ = slices[2][0]
        c3_ = slices[3][0]
        c4_ = slices[4][0]
        c5_ = slices[5][0]
    module_template = module_template.format(
        rt1=MODULE_TEMPLATE_1,
        rt2=MODULE_TEMPLATE_2,
        rt3=MODULE_TEMPLATE_3,
        rt4=MODULE_TEMPLATE_4,
        bc=BEGIN_CODE,
        ec=END_CODE,
        c1_=c1_,
        c2_=c2_,
        c3_=c3_,
        c4_=c4_,
        c5_=c5_
    )
    return module_template

def update_this_module(model, relation, package_dir, package_name, dirs_list):
    """Updates the module."""
    _, fqtn = relation.split()
    path = fqtn.split('.')

    fqtn = '.'.join(path[1:])
    rel = model.get_relation_class(fqtn)()

    path[0] = package_dir
    module_path = '{}.py'.format('/'.join(
        [iskeyword(elt) and "{}_".format(elt) or elt for elt in path]))
    schema_dir = os.path.dirname(module_path)
    if not schema_dir in dirs_list:
        dirs_list.append(schema_dir)
    module_name = path[-1]
    path = '/'.join(path[:-1])
    if not os.path.exists(path):
        os.makedirs(path)
    module_template = make_module(module_path)
    inheritance_import, inherited_classes = get_inheritance_info(
        rel, package_name)
    open(module_path, 'w').write(
        module_template.format(
            module="{}.{}".format(package_name, fqtn),
            package_name=package_name,
            documentation="\n".join(["    {}".format(line)
                                     for line in str(rel).split("\n")]),
            inheritance_import=inheritance_import,
            inherited_classes=inherited_classes,
            class_name=camel_case(module_name), fqtn=fqtn))
    return module_path

def update_modules(model, package_dir, package_name):
    """Synchronize the modules with the structure of the relation in PG.
    """
    dirs_list = []
    files_list = []

    for relation in model._relations():
        module_path = update_this_module(
            model, relation, package_dir, package_name, dirs_list)
        files_list.append(module_path)

    return files_list

def update_init_files(package_name, files_list):
    """Update __all__ lists in __init__ files.
    """
    for root, dirs, files in os.walk('{}/{}'.format(package_name, package_name)):
        all_ = []
        for dir_ in dirs:
            if dir_ != '__pycache__':
                all_.append(dir_)
        for file in files:
            path_ = "{}/{}".format(root, file)
            if path_ not in files_list and file not in DO_NOT_REMOVE:
                print("REMOVING: {}".format(path_))
                os.remove(path_)
                continue
            if (re.findall('.py$', file) and
                    file != '__init__.py' and
                    file != '__pycache__'):
                all_.append(file.replace('.py', ''))
        all_.sort()
        open('{}/__init__.py'.format(root), 'w').write(
            '__all__ = {}\n'.format(all_))

def main():
    """Script entry point"""
    import argparse

    rel_package = None
    config_file, package_name = load_config_file()
    if config_file:
        rel_package = "."

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=AP_DESCRIPTION,
        epilog=AP_EPILOG)
    #group = parser.add_mutually_exclusive_group()
    parser.add_argument(
        "-p", "--package_name", nargs="?", const="",
        help="Python package name default to DB_NAME"
    )
    parser.add_argument(
        "-c", "--config_file", nargs="?", const=None,
        help="half_orm config file (in /etc/half_orm)")
    args = parser.parse_args()
    if config_file and args.config_file:
        sys.stderr.write(
            "You are in a halfORM package directory.\n"
            "Try halfORM without argument.\n")
        sys.exit(1)
    if args.config_file:
        config_file = args.config_file
        package_name = (
            args.package_name and args.package_name or args.config_file)
    try:
        assert config_file
    except AssertionError:
        sys.stderr.write(
            "You're not in a halfORM package directory.\n"
            "Try halfORM --help.\n")
        sys.exit(1)
    model = Model(config_file)

    try:
        open('/etc/half_orm/{}'.format(config_file))
    except FileNotFoundError as err:
        sys.stderr.write('{}\n'.format(err))
        sys.stderr.write('Config file must be in /etc/half_orm/ directory!\n')
        sys.exit(1)

    package_dir = "{}/{}".format(rel_package or package_name, package_name)

    if not rel_package:
        init_package(model, package_dir, package_name)
    files_list = update_modules(model, package_dir, package_name)
    update_init_files(package_name, files_list)

if __name__ == '__main__':
    main()
