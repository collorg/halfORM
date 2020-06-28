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
from half_orm import relation_errors

class ClassInstanciationError(Exception):
    "Failed to instanciate a relation class"
    def __init__(self, msg):
        super().__init__(msg)

HALFORM_PATH = os.path.dirname(__file__)
BEGIN_CODE = "#>>> PLACE YOUR CODE BELLOW THIS LINE. DO NOT REMOVE THIS LINE!\n"
END_CODE = "#<<< PLACE YOUR CODE ABOVE THIS LINE. DO NOT REMOVE THIS LINE!\n"
README = open('{}/halfORM_templates/README'.format(HALFORM_PATH)).read()
CONFIG_TEMPLATE = open(
    '{}/halfORM_templates/config'.format(HALFORM_PATH)).read()
SETUP_TEMPLATE = open(
    '{}/halfORM_templates/setup.py'.format(HALFORM_PATH)).read()
DB_CONNECTOR_TEMPLATE = open(
    '{}/halfORM_templates/db_connector.py'.format(HALFORM_PATH)).read()
MODULE_TEMPLATE_1 = open(
    '{}/halfORM_templates/module_template_1'.format(HALFORM_PATH)
    ).read()
MODULE_TEMPLATE_2 = open(
    '{}/halfORM_templates/module_template_2'.format(HALFORM_PATH)).read()
MODULE_TEMPLATE_3 = open(
    '{}/halfORM_templates/module_template_3'.format(HALFORM_PATH)).read()
WARING_TEMPLATE = open(
    '{}/halfORM_templates/warning'.format(HALFORM_PATH)).read()
MODULE_FORMAT = (
    "{rt1}{bc_}{global_user_s_code}{ec_}{rt2}{rt3}\n        {bc_}{user_s_code}")
AP_DESCRIPTION = """Generates python package from a PG database"""
AP_EPILOG = """"""
DO_NOT_REMOVE = ['db_connector.py', '__init__.py']

def hop_update():
    """Rename some files an directories. hop upgrade.
    """
    if os.path.exists('.halfORM'):
        os.rename('.halfORM', '.hop')
        sys.stderr.write('WARNING! Renaming .halfORM to .hop.')
    if os.path.exists('README.rst'):
        os.rename('README.rst', 'README.md')
    lines = []
    with open('setup.py') as setup_file:
        for line in setup_file:
            if line.find('README.rst'):
                line = line.replace('README.rst', 'README.md')
            lines.append(line)
    open('setup.py', 'w').write(''.join(lines))

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
    for base in ['hop', 'halfORM']:
        if os.path.exists('.{}/config'.format(base)):
            config.read('.{}/config'.format(base))
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
    os.makedirs('{}/.hop'.format(package_name))
    open('{}/.hop/config'.format(package_name), 'w').write(
        CONFIG_TEMPLATE.format(
            config_file=model._dbinfo['name'], package_name=package_name))
    readme_file_name = '{}/README.md'.format(package_name)
    cmd = " ".join(sys.argv)
    readme = README.format(cmd=cmd, dbname=dbname, package_name=package_name)
    open(readme_file_name, 'w').write(readme)

def get_inheritance_info(rel, package_name):
    """Returns inheritance informations for the rel relation.
    """
    inheritance_import_list = []
    inherited_classes_aliases_list = []
    for base in rel.__class__.__bases__:
        if base.__name__ != 'Relation':
            inh_sfqrn = list(base.__sfqrn)
            inh_sfqrn[0] = package_name
            inh_cl_alias = "{}{}".format(
                camel_case(inh_sfqrn[1]), camel_case(inh_sfqrn[2]))
            inh_cl_name = "{}".format(camel_case(inh_sfqrn[2]))
            inheritance_import_list.append(
                "from {} import {} as {}".format(".".join(
                    inh_sfqrn), inh_cl_name, inh_cl_alias)
            )
            inherited_classes_aliases_list.append(inh_cl_alias)
    inheritance_import = "\n".join(inheritance_import_list)
    inherited_classes = ", ".join(inherited_classes_aliases_list)
    if inherited_classes.strip():
        inherited_classes = "{},".format(inherited_classes)
    return inheritance_import, inherited_classes

def assemble_module_template(module_path):
    """Construct the module after slicing it if it already exists.
    """
    user_s_code = ""
    global_user_s_code = "\n"
    module_template = MODULE_FORMAT
    if os.path.exists(module_path):
        module_code = open(module_path).read()
        user_s_code = module_code.rsplit(BEGIN_CODE, 1)[1]
        user_s_code = user_s_code.replace('{', '{{').replace('}', '}}')
        global_user_s_code = module_code.rsplit(END_CODE)[0].split(BEGIN_CODE)[1]
        global_user_s_code = global_user_s_code.replace('{', '{{').replace('}', '}}')
    return module_template.format(
        rt1=MODULE_TEMPLATE_1, rt2=MODULE_TEMPLATE_2, rt3=MODULE_TEMPLATE_3,
        bc_=BEGIN_CODE, ec_=END_CODE,
        global_user_s_code=global_user_s_code, user_s_code=user_s_code)

def update_this_module(
        model, relation, package_dir, package_name, dirs_list, warning):
    """Updates the module."""
    _, fqtn = relation.split()
    path = fqtn.split('.')

    fqtn = '.'.join(path[1:])
    try:
        rel = model.get_relation_class(fqtn)()
    except TypeError as err:
        sys.stderr.write("{}\n{}\n".format(err, fqtn))
        sys.stderr.flush()
        return None

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
    module_template = assemble_module_template(module_path)
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
            class_name=camel_case(module_name),
            fqtn=fqtn,
            warning=warning))
    return module_path

def update_modules(model, package_dir, package_name, warning):
    """Synchronize the modules with the structure of the relation in PG.
    """
    dirs_list = []
    files_list = []

    dbname = model._dbname
    open('{}/db_connector.py'.format(package_dir), 'w').write(
        DB_CONNECTOR_TEMPLATE.format(dbname=dbname, package_name=package_name))
    for relation in model._relations():
        module_path = update_this_module(
            model, relation, package_dir, package_name, dirs_list, warning)
        if module_path:
            files_list.append(module_path)

    return files_list

def update_init_files(package_dir, warning, files_list):
    """Update __all__ lists in __init__ files.
    """
    for root, dirs, files in os.walk(package_dir):
        all_ = []
        for dir_ in dirs:
            if dir_ != '__pycache__':
                all_.append(dir_)
        for file in files:
            path_ = "{}/{}".format(root, file)
            if path_ not in files_list and file not in DO_NOT_REMOVE:
                if path_.find('__pycache__') == -1:
                    print("REMOVING: {}".format(path_))
                os.remove(path_)
                continue
            if (re.findall('.py$', file) and
                    file != '__init__.py' and
                    file != '__pycache__'):
                all_.append(file.replace('.py', ''))
        all_.sort()
        with open('{}/__init__.py'.format(root), 'w') as init_file:
            init_file.write('"""{}"""\n\n'.format(warning))
            init_file.write(
                '__all__ = [\n    {}\n]\n'.format(",\n    ".join(
                    ["'{}'".format(elt) for elt in all_])))

def test_package(model, package_dir, package_name):
    """Basic testing of each relation module in the package.
    The class should instanciate.
    """
    import importlib

    dbname = model._dbname
    open('{}/db_connector.py'.format(package_dir), 'w').write(
        DB_CONNECTOR_TEMPLATE.format(dbname=dbname, package_name=package_name))
    for relation in model._relations():
        fqtn = relation.split('.')[1:]
        module_name = f'.{fqtn[-1]}'
        class_name = camel_case(fqtn[-1])
        fqtn = '.'.join(fqtn[:-1])
        file_path = f'.{package_dir.split("/")[1]}.{fqtn}'

        try:
            module = importlib.import_module(module_name, file_path)
            _ = module.__dict__[class_name]()
        except relation_errors.DuplicateAttributeError as err:
            print(err)
        except relation_errors.IsFrozenError as err:
            print(err)
        except Exception as err:
            print(f'ERROR in class {file_path}.{class_name}!\n{err}')

def main():
    """Script entry point"""
    import argparse

    sys.path.insert(0, os.getcwd())

    rel_package = None
    config_file, package_name = load_config_file()
    if config_file:
        rel_package = "."

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=AP_DESCRIPTION,
        epilog=AP_EPILOG)

    parser.add_argument(
        "-p", "--package_name", nargs="?", const="",
        help="Python package name default to DB_NAME"
    )

    parser.add_argument(
        "-c", "--config_file", nargs="?", const=None,
        help="half_orm config file (in /etc/half_orm if no / in the name provided)"
    )

    parser.add_argument(
        "-t", "--test", nargs="?", const="test", help="Test some common pitfalls."
    )

    args = parser.parse_args()
    if config_file and args.config_file:
        sys.stderr.write(
            "You are in a halfORM package directory.\n"
            "Try hop without argument.\n")
        sys.exit(1)

    if args.config_file:
        config_file = args.config_file

        package_name = (
            args.package_name if args.package_name else args.config_file)

    try:
        if config_file
        model = Model()
    except Exception as e:
        sys.stderr.write(
            "You're not in a halfORM package directory.\n"
            "Try hop --help.\n")
        sys.exit(1)
    try:
        base = '/etc/half_orm/'
        if config_file.find('/') != -1:
            base = ''
        open('{}{}'.format(base, config_file))
    except FileNotFoundError as err:
        sys.stderr.write('{}\n'.format(err))
        sys.exit(1)

    package_dir = "{}/{}".format(rel_package or package_name, package_name)

    warning = WARING_TEMPLATE.format(package_name=package_name)

    if not rel_package:
        init_package(model, package_dir, package_name)
    files_list = update_modules(model, package_dir, package_name, warning)
    update_init_files(package_dir, warning, files_list)
    if not args.config_file:
        hop_update()
        test_package(model, package_dir, package_name)

if __name__ == '__main__':
    main()
