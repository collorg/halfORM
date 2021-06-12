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
import subprocess
import sys
from keyword import iskeyword
from getpass import getpass
from configparser import ConfigParser

import psycopg2
from git import Repo, GitCommandError

import click

from half_orm.model import Model, camel_case, CONF_DIR
from half_orm.model_errors import MissingConfigFile
from .patch import Patch
from .test import tests

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
FKEYS_PROPS = open('fkeys_properties').read()
WARNING_TEMPLATE = open('warning').read()
BASE_TEST = open('base_test').read()
TEST = open('relation_test').read()
os.chdir(BASE_DIR)

MODULE_FORMAT = (
    "{rt1}{bc_}{global_user_s_code}{ec_}{rt2}{rt3}\n        {bc_}{user_s_code}")
AP_EPILOG = """"""
DO_NOT_REMOVE = ['db_connector.py', '__init__.py', 'base_test.py']

MODEL = None

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
    config = ConfigParser()

    if not base_dir:
        ref_dir = os.path.abspath(os.path.curdir)
        base_dir = ref_dir
    for base in ['hop', 'halfORM']:
        if os.path.exists('.{}/config'.format(base)):
            config.read('.{}/config'.format(base))
            config_file = config['halfORM']['config_file']
            return config_file

    if os.path.abspath(os.path.curdir) != '/':
        os.chdir('..')
        cur_dir = os.path.abspath(os.path.curdir)
        return load_config_file(cur_dir, ref_dir)
    # restore reference directory.
    os.chdir(ref_dir)
    return None

def init_package(model, project_name: str):
    """Initialises the package directory.

    model (Model): The loaded model instance
    project_name (str): The project name (hop create argument)
    """
    curdir = os.path.abspath(os.curdir)
    os.chdir(TEMPLATES_DIR)
    README = open('README').read()
    CONFIG_TEMPLATE = open('config').read()
    SETUP_TEMPLATE = open('setup.py').read()
    GIT_IGNORE = open('.gitignore').read()
    PIPFILE = open('Pipfile').read()
    project_path = os.path.join(curdir, project_name)
    if not os.path.exists(project_path):
        os.makedirs(project_path)
    else:
        raise Exception(f'The path {project_path} already exists')

    os.chdir(project_path)

    dbname = model._dbname
    setup = SETUP_TEMPLATE.format(dbname=dbname, package_name=project_name)
    open('./setup.py', 'w').write(setup)
    open('./Pipfile', 'w').write(PIPFILE)
    os.makedirs('./.hop')
    open(f'./.hop/config', 'w').write(
        CONFIG_TEMPLATE.format(
            config_file=project_name, package_name=project_name))
    cmd = " ".join(sys.argv)
    readme = README.format(cmd=cmd, dbname=dbname, package_name=project_name)
    open('./README.md', 'w').write(readme)
    open('./.gitignore', 'w').write(GIT_IGNORE)
    os.mkdir(f'./{project_name}')
    try:
        Repo.init('.', initial_branch='main')
        print("Initializing git with a 'main' branch.")
    except GitCommandError:
        Repo.init('.')
        print("Initializing git with a 'master' branch.")

    repo = Repo('.')
    Patch(model, create_mode=True).patch()
    model.reconnect() # we get the new stuff from db metadata here
    subprocess.run(['hop', 'update', '-f']) # hop creates/updates the modules & ignore tests

    try:
        repo.head.commit
    except ValueError:
        repo.git.add('.')
        repo.git.commit(m='[0.0.0] First release')

    print("Switching to the 'devel' branch.")
    repo.git.checkout(b='devel')

def get_fkeys(rel):
    """
    """
    fks = '\n    '.join([f"('', '{key}')," for key in rel._fkeys])
    if fks:
        return FKEYS_PROPS.format(fks)
    return ''

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
            fkeys_properties=get_fkeys(rel),
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
            TEST.format(
                package_name=package_name,
                module=module,
                class_name=camel_case(module_name))
        )
    return module_path

def update_modules(model, warning):
    """Synchronize the modules with the structure of the relation in PG.
    """
    dirs_list = []
    files_list = []

    dbname = model._dbname
    package_dir = package_name = model.package_name
    open(f'{package_dir}/db_connector.py', 'w').write(
        DB_CONNECTOR_TEMPLATE.format(dbname=dbname, package_name=package_name))

    if not os.path.exists(f'{package_dir}/base_test.py'):
        open(f'{package_dir}/base_test.py', 'w').write(
            BASE_TEST.format(package_name=package_name)
        )
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
    exp = re.compile('/[A-Z]')
    for root, dirs, files in os.walk(package_dir):
        all_ = []
        if exp.search(root):
            continue

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

def set_config_file(project_name: str):
    """ Asks for the connection parameters. Returns a dictionary with the params.
    """


    conf_path = os.path.join(CONF_DIR, project_name)
    if not os.path.isfile(conf_path):
        if not os.access(CONF_DIR, os.W_OK):
            sys.stderr.write(f"You don't have write acces to {CONF_DIR}.\n")
            if CONF_DIR == '/etc/half_orm':
                sys.stderr.write(
                    "Set the HALFORM_CONF_DIR environment variable if you want to use a\n"
                    "different directory.\n")
            sys.exit(1)
        dbname = input(f'Database ({project_name}): ') or project_name
        print(f'Input the connection parameters to the {dbname} database.')
        user = os.environ['USER']
        user = input(f'User ({user}): ') or user
        password = getpass('Password: ')
        if len(password) == 0 and \
            (input('Is it an ident login with a local account? [Y/n]') or 'Y') == 'Y':
                host = port = ''
        else:
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
        open(f'{CONF_DIR}/{project_name}', 'w').write(TMPL_CONF_FILE.format(**res))


    try:
        return Model(project_name)
    except psycopg2.OperationalError:
        config = ConfigParser()
        config.read([ conf_path ])
        dbname = config.get('database', 'name')

        sys.stderr.write(f'The {dbname} database does not exist.\n')
        create = input('Do you want to create it (N/y): ') or "n"
        if create.upper() == 'Y':
            subprocess.run(['createdb', dbname])
            model = Model(project_name)
            return model
        sys.exit(1)

@click.group(invoke_without_command=True)
@click.option('-v', '--version', is_flag=True)
def main(version):
    """
    Generates/Synchronises/Patches a python package from a PostgreSQL database
    """
    from half_orm import __version__
    if version:
        click.echo(f'halfORM {__version__}')
        sys.exit()

    sys.path.insert(0, '.')



@main.command()
@click.argument('package_name')
def create(package_name):
    """ Creates a hop project named <package_name>
    It adds to your database a patch system (by creating the relations:
    meta.release, meta.release_issue and the view "meta.view".last_release)
    """
    click.echo(f'hop create {package_name}')
    # on cherche un fichier de conf .hop/config dans l'arbre.
    model = set_config_file(package_name)

    init_package(model, package_name)


def get_model():
    config_file = load_config_file()

    if not config_file:
        sys.stderr.write(
            "You're not in a halfORM package directory.\n"
            "Try hop --help.\n")
        sys.exit(1)

    try:
        return Model(config_file)
    except psycopg2.OperationalError as exc:
        sys.stderr.write(f'The database {config_file} does not exist.\n')
        raise exc
    except MissingConfigFile:
        sys.stderr.write(f'Cannot find the half_orm config file for this database.\n')
        sys.exit(1)


@main.command()
def init():
    """ Initialize a cloned hop project by applying the base patch
    """
    model = get_model()
    Patch(model, init_mode=True).patch()
    sys.exit()


@main.command()
def patch():
    """ Apply the next patch
    """

    model = get_model()
    Patch(model).patch()


    sys.exit()


@main.command()
@click.option('-f', '--force', is_flag=True, help='Updates the package without testing')
def update(force):
    model = get_model()
    if force or tests(model):
        files_list = update_modules(model, '')
        update_init_files(model.package_name, '', files_list)
    else:
        print("\nPlease correct the errors before proceeding!")
        sys.exit(1)


@main.command()
def test():
    """ Test some common pitfalls.
    """
    model = get_model()
    if tests(model):
        click.echo('Tests OK')
    else:
        click.echo('Tests failed')


if __name__ == '__main__':
    main()
