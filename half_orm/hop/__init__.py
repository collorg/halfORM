#!/usr/bin/env python3
#-*- coding: utf-8 -*-
# pylint: disable=invalid-name, protected-access

"""
Generates/Patches/Synchronizes a hop Python package with a PostgreSQL database
with the `hop` command.

`hop -c <dbname>` creates a hop project for the <dbname> database. It adds to
your database a patch system (by creating the relations: meta.release,
meta.release_issue and the view "meta.view".last_release).

In the dbname directory generated, the hop command helps you patch, test and
deal with CI.

On the 'devel' or any private branch hop applies patches if any, runs tests.
On the 'main' or 'master' branch, hop checks that your git repo is in sync with
the remote origin, synchronizes with devel branch if needed and tags your git
history with the last release applied.
"""

import re
import os
import subprocess
import sys
from keyword import iskeyword
from getpass import getpass

import psycopg2
from git import Repo, GitCommandError

from half_orm.model import Model, camel_case, CONF_DIR
from half_orm.model_errors import MissingConfigFile
from half_orm import relation_errors
from .patch import patch

BASE_DIR = os.getcwd()

TMPL_CONF_FILE = """[database]
name = {name}
user = {user}
password = {password}
host = {host}
port = {port}
production = {production}
"""

HALFORM_PATH = os.path.dirname(__file__)
BEGIN_CODE = "#>>> PLACE YOUR CODE BELLOW THIS LINE. DO NOT REMOVE THIS LINE!\n"
END_CODE = "#<<< PLACE YOUR CODE ABOVE THIS LINE. DO NOT REMOVE THIS LINE!\n"

TEMPLATES_DIR = f'{HALFORM_PATH}/templates'

os.chdir(TEMPLATES_DIR)
DB_CONNECTOR_TEMPLATE = open('db_connector.py').read()
MODULE_TEMPLATE_1 = open('module_template_1').read()
MODULE_TEMPLATE_2 = open('module_template_2').read()
MODULE_TEMPLATE_3 = open('module_template_3').read()
WARNING_TEMPLATE = open('warning').read()
TEST = open('relation_test').read()
os.chdir(BASE_DIR)

MODULE_FORMAT = (
    "{rt1}{bc_}{global_user_s_code}{ec_}{rt2}{rt3}\n        {bc_}{user_s_code}")
AP_DESCRIPTION = """
Generates/Synchronises/Patches a python package from a PostgreSQL database
"""
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

def init_package(model, base_dir, name):
    """Initialises the package directory.
    """
    curdir = os.path.abspath(os.curdir)
    os.chdir(TEMPLATES_DIR)
    README = open('README').read()
    CONFIG_TEMPLATE = open('config').read()
    SETUP_TEMPLATE = open('setup.py').read()
    GIT_IGNORE = open('.gitignore').read()
    PIPFILE = open('Pipfile').read()
    os.chdir(curdir)
    dbname = model._dbname
    if not os.path.exists(name):
        os.makedirs(base_dir)
        setup = SETUP_TEMPLATE.format(dbname=dbname, package_name=name)
        setup_file_name = f'{name}/setup.py'
        if not os.path.exists(setup_file_name):
            open(setup_file_name, 'w').write(setup)
        open(f'{name}/Pipfile', 'w').write(PIPFILE)
    os.makedirs(f'{name}/.hop')
    open(f'{name}/.hop/config', 'w').write(
        CONFIG_TEMPLATE.format(
            config_file=model._dbinfo['name'], package_name=name))
    cmd = " ".join(sys.argv)
    readme = README.format(cmd=cmd, dbname=dbname, package_name=name)
    open(f'{name}/README.md', 'w').write(readme)
    open(f'{name}/.gitignore', 'w').write(GIT_IGNORE)
    os.mkdir(f'{name}/{name}')
    os.chdir(name)
    if not os.path.isdir('.git'):
        try:
            Repo.init('.', initial_branch='main')
            print("Initializing git with a 'main' branch.")
        except GitCommandError:
            Repo.init('.')
            print("Initializing git with a 'master' branch.")
    repo = Repo('.')
    release = patch(name, create=True)
    model.reconnect() # we get the new stuff from db metadata here
    subprocess.run(['hop']) # hop creates/updates the modules
    try:
        repo.head.commit
    except ValueError:
        repo.git.add('.')
        repo.git.commit(m='[0.0.0] First release')
    print("Switching to the 'devel' branch.")
    repo.git.checkout(b='devel')
    os.chdir('..')

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
    module = f"{package_name}.{fqtn}"
    open(module_path, 'w').write(
        module_template.format(
            module=module,
            package_name=package_name,
            documentation="\n".join(["    {}".format(line)
                                     for line in str(rel).split("\n")]),
            inheritance_import=inheritance_import,
            inherited_classes=inherited_classes,
            class_name=camel_case(module_name),
            fqtn=fqtn,
            warning=warning))
    test_path = module_path.replace('.py', '_test.py')
    if not os.path.exists(test_path):
        open(test_path, 'w').write(
            TEST.format(module=module, class_name=camel_case(module_name))
        )
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
            if module_path.find('__init__.py') == -1:
                test_file_path = module_path.replace('.py', '_test.py')
                files_list.append(test_file_path)

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
                if path_.find('__pycache__') == -1 and path_.find('_test.py') == -1:
                    print("REMOVING: {}".format(path_))
                os.remove(path_)
                continue
            if (re.findall('.py$', file) and
                    file != '__init__.py' and
                    file != '__pycache__' and
                    file.find('_test.py') == -1):
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

def set_config_file(dbname: str) -> dict:
    """Asks for the connection parameters. Returns a dictionary with the params.
    """
    if not os.access(CONF_DIR, os.W_OK):
        sys.stderr.write(f"You don't have write acces to {CONF_DIR}.\n")
        if CONF_DIR == '/etc/half_orm':
            sys.stderr.write(
                "Set the HALFORM_CONF_DIR environment variable if you want to use a\n"
                "different directory.\n")
        sys.exit(1)
    print(f'Input the connection parameters to the {dbname} database.')
    user = os.environ['USER']
    user = input(f'User ({user}): ') or user
    password = getpass('Password: ')
    host = input('Host (localhost): ') or 'localhost'
    port = input('Port (5432): ') or 5432
    production = input('Production (False): ') or False
    res = {
        'name': dbname,
        'user': user,
        'password': password,
        'host': host,
        'port': port,
        'production': production
        }
    open(f'{CONF_DIR}/{dbname}', 'w').write(TMPL_CONF_FILE.format(**res))
    try:
        return Model(dbname)
    except psycopg2.OperationalError:
        sys.stderr.write(f'The {dbname} database does not exist.\n')
        create = input('Do you want to create it (N/y): ') or "n"
        if create.upper() == 'Y':
            subprocess.run(['createdb', dbname])
            model = Model(dbname)
            return model
        sys.exit(1)

def main():
    """Script entry point"""
    import argparse

    sys.path.insert(0, os.getcwd())

    parser = argparse.ArgumentParser(
        description=AP_DESCRIPTION,
        epilog=AP_EPILOG)
    parser.add_argument(
        "-p", "--patch", type=bool, const=True, default=False,
        nargs="?", help="Install or use the patch system"
    )
    parser.add_argument(
        "-c", "--create", nargs="?", const=None,
        help="half_orm config file name")
    # group = parser.add_mutually_exclusive_group()
    # group.add_argument('--patch')
    # group.add_argument('--create')
    parser.add_argument(
        "-t", "--test", nargs="?", const="test", help="Test some common pitfalls."
    )
    try:
        args = parser.parse_args()
    except IndexError:
        parser.print_help()
        sys.exit(1)
    rel_package = None
    # on cherche un fichier de conf .hop/config dans l'arbre.
    config_file, package_name = load_config_file()
    if config_file:
        rel_package = "."

    if config_file and args.create:
        sys.stderr.write(
            "You are in a halfORM package directory.\n")
        sys.exit(1)
    if args.create:
        config_file = args.create
    if not config_file:
        sys.stderr.write(
            "You're not in a halfORM package directory.\n"
            "Try hop --help.\n")
        sys.exit(1)
    try:
        model = Model(config_file)
    except psycopg2.OperationalError:
        sys.stderr.write(f'The database {config_file} does not exist.\n')
        sys.exit(1)
    except MissingConfigFile:
        model = set_config_file(args.create)

    try:
        open('{}/{}'.format(CONF_DIR, config_file))
    except FileNotFoundError as err:
        sys.stderr.write('ERROR! No such config file: {}\n'.format(err))
        sys.exit(1)
    if args.patch:
        patch(model._dbname)
        sys.exit()

    name = None
    if args.create:
        package_dir = args.create
        package_name = args.create
        init_package(model, package_dir, package_name)
    name = name or package_name
    package_dir = "{}/{}".format(rel_package or name, name)
    warning = WARNING_TEMPLATE.format(package_name=name)

    files_list = update_modules(model, package_dir, name, warning)
    update_init_files(package_dir, warning, files_list)
    # if not args.create:
    #     hop_update()
    #     test_package(model, package_dir, name)

if __name__ == '__main__':
    main()
