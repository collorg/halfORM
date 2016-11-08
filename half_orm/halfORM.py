#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""\
Generates a python package from a PostgreSQL database
"""

import re
import os
import sys
from keyword import iskeyword

from half_orm.model import Model

README = '''\
half_orm package for the '{dbname}' database.

This package has been generated automatically by halfORM
(https://github.com/collorg/halfORM)

DO NOT ADD OR REMOVE ANY FILE IN {package_name} DIRECTORY.
It is the exact representation of the model of the '{dbname}' database.

Rerun the command:

{cmd}

in the parent directory if you make any changes in your
database model. It will synchronize the modules in this
package.
'''

SETUP_TEMPLATE = '''\
"""Package for PostgreSQL {dbname} database.
"""

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='{package_name}',

    version='0.0.0',

    description='Package for {dbname} PG',
    long_description=long_description,

    # url='',

    # author='',
    # author_email='',

    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],

    keywords='',

    packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    install_requires=['half_orm'],

)
'''

DB_CONNECTOR_TEMPLATE = """\
#-*- coding: utf-8 -*-

__all__ = ['model']

from half_orm.model import Model

model = Model('{dbname}')
"""

BEGIN_CODE = "#>>> Place your code bellow\n"
END_CODE = "#<<< Place your code above\n"
BEGIN_CODE_I = "#>>> Place your code bellow"
END_CODE_I = "#<<< Place your code above"

MODULE_TEMPLATE_1 = """\
#-*- coding: utf-8 -*-

'''The module {{module}} povides the {{class_name}} class.

This module has been generated by halfORM
see https://github.com/collorg/halfORM for more on half_orm

Place your code between:
{bc_i}
this is your code
{ec_i}

or at the end of the file after
{ec_i}

DO NOT REMOVE, ADD OR MODIFY the lines:
{bc_i}
{ec_i}
'''

from {{package_name}}.db_connector import model
{{inheritance_import}}
""".format(bc_i=BEGIN_CODE_I, ec_i=END_CODE_I)

MODULE_TEMPLATE_2 = """\

__RCLS = model.relation('{fqtn}').__class__

class {class_name}(__RCLS, {inherited_classes}):
    '''\\
{documentation}
    '''
    \
"""

MODULE_TEMPLATE_3 = """\
    def __init__(self, **kwargs):
        \
"""

MODULE_TEMPLATE_4 = """\
        super({class_name}, self).__init__(**kwargs)

    \
"""

MODULE_FORMAT_1 = (
    "{rt1}{bc}{c1}{ec}{rt2}{bc}{c2}    {ec}{rt3}{bc}{c3}        {ec}{rt4}{bc}{c4}")
MODULE_FORMAT_2 = (
    "{rt1}{bc}{c1}{ec}{rt2}{bc}{c2}{ec}{rt3}{bc}{c3}{ec}{rt4}{bc}{c4}")

AP_DESCRIPTION = """Generates python package from a PG database"""
AP_EPILOG = """"""

DO_NOT_REMOVE = ['db_connector.py', '__init__.py']
def camel_case(name):
    """Transform a string in camel case."""
    ccname = []
    name = name.lower()
    capitalize = True
    for char in name:
        if not char.isalnum():
            capitalize = True
            continue
        if capitalize:
            ccname.append(char.upper())
            capitalize = False
            continue
        ccname.append(char)
    return ''.join(ccname)

def main():
    """Script entry point"""
    import argparse

    files_list = []
    dirs_list = []

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=AP_DESCRIPTION,
        epilog=AP_EPILOG)
    #group = parser.add_mutually_exclusive_group()
    parser.add_argument(
        "-p", "--package_name", help="Python package name default to DB_NAME"
    )
    parser.add_argument(
        "-c", "--config_file",
        help="Configuration file to connect to DB_NAME. Must be in /etc/half_orm"
    )
    parser.add_argument("db_name", help="Database name")
    args = parser.parse_args()
    dbname = args.db_name
    package_name = args.package_name and args.package_name or args.db_name
    config_file = args.config_file and args.config_file or args.db_name

    try:
        open('/etc/half_orm/{}'.format(config_file))
    except FileNotFoundError as err:
        sys.stderr.write('{}\n'.format(err))
        sys.stderr.write('Config file must be in /etc/half_orm/ directory!\n')
        sys.exit(1)

    if not os.path.exists(package_name):
        package_dir = "{}/{}".format(package_name, package_name)
        os.makedirs(package_dir)
        cmd = " ".join(sys.argv)
        setup = SETUP_TEMPLATE.format(dbname=dbname, package_name=package_name)
        readme = README.format(cmd=cmd, dbname=dbname, package_name=package_name)
        readme_file_name = '{}/README.rst'.format(package_name)
        if not os.path.exists(readme_file_name):
            open(readme_file_name, 'w').write(readme)
        setup_file_name = '{}/setup.py'.format(package_name)
        if not os.path.exists(setup_file_name):
            open(setup_file_name, 'w').write(setup)
        open('{}/db_connector.py'.format(package_dir), 'w').write(
            DB_CONNECTOR_TEMPLATE.format(
                dbname=dbname, package_name=package_name))

    model = Model(args.db_name)
    for relation in model._relations():
        _, fqtn = relation.split()
        path = fqtn.split('.')

        fqtn = '.'.join(path[1:])
        rel = model.relation(fqtn)
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

        module = "{}.{}".format(package_name, fqtn)
        path[0] = "{}/{}".format(package_name, package_name)
        module_path = '{}.py'.format('/'.join(
            [iskeyword(elt) and "{}_".format(elt) or elt for elt in path]))
        schema_dir = os.path.dirname(module_path)
        if not schema_dir in dirs_list:
            dirs_list.append(schema_dir)
        module_name = path[-1]
        path = '/'.join(path[:-1])
        if not os.path.exists(path):
            os.makedirs(path)
        c1 = ""
        c2 = ""
        c3 = ""
        c4 = ""
        MODULE_TEMPLATE = MODULE_FORMAT_1
        if os.path.exists(module_path):
            MODULE_TEMPLATE = MODULE_FORMAT_2
            slices = [elt.split(END_CODE)
                      for elt in open(module_path).read().split(BEGIN_CODE)]
            c1 = slices[1][0]
            c2 = slices[2][0]
            c3 = slices[3][0]
            c4 = slices[4][0]
        module_template = MODULE_TEMPLATE.format(
            rt1=MODULE_TEMPLATE_1,
            rt2=MODULE_TEMPLATE_2,
            rt3=MODULE_TEMPLATE_3,
            rt4=MODULE_TEMPLATE_4,
            bc=BEGIN_CODE,
            ec=END_CODE,
            c1=c1,
            c2=c2,
            c3=c3,
            c4=c4
        )
        documentation = "\n".join(["    {}".format(line)
                                   for line in str(rel).split("\n")])
        files_list.append(module_path)
        open(module_path, 'w').write(
            module_template.format(
                module=module,
                package_name=package_name,
                documentation=documentation,
                inheritance_import=inheritance_import,
                inherited_classes=inherited_classes,
                class_name=camel_case(module_name), fqtn=fqtn))

    for root, dirs, files in os.walk('{}/{}'.format(package_name, package_name)):
        all_ = []
        for dir_ in dirs:
            if dir_ != '__pycache__':
                all_.append(dir_)
        for file in files:
            path_ = "{}/{}".format(root, file)
            if not path_ in files_list and file not in DO_NOT_REMOVE:
                print("REMOVING: {}".format(path_))
                os.remove(path_)
                continue
            if (re.findall('.py$', file) and
                file != '__init__.py' and
                file != '__pycache__'):
                all_.append(file.replace('.py', ''))
        open('{}/__init__.py'.format(root), 'w').write(
            '__all__ = {}\n'.format(all_))

if __name__ == '__main__':
    main()
