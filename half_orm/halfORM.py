#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""\
Generates a python package from a PostgreSQL database
"""

import re
import os
import sys

from half_orm.model import Model

README = '''\
Package for PostgreSQL {dbname} database.
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

RELATION_TEMPLATE = """\
#-*- coding: utf-8 -*-

from {package_name}.db_connector import model

class {class_name}:
    __model = model
    def __new__(cls, **kwargs):
        return cls.__model.relation('{fqtn}', **kwargs)
"""

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

AP_DESCRIPTION = """Generates python package from a PG database"""
AP_EPILOG = """"""

def main():
    """Script entry point"""
    import argparse

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
        setup = SETUP_TEMPLATE.format(dbname=dbname, package_name=package_name)
        readme = README.format(dbname=dbname)
        open('{}/README.rst'.format(package_name), 'w').write(readme)
        open('{}/setup.py'.format(package_name), 'w').write(setup)
        open('{}/db_connector.py'.format(package_dir), 'w').write(
            DB_CONNECTOR_TEMPLATE.format(
                dbname=dbname, package_name=package_name))

    model = Model(args.db_name)
    for relation in model.relations():
        _, fqtn = relation.split()
        path = fqtn.split('.')

        fqtn = '.'.join(path[1:])

        path[0] = "{}/{}".format(package_name, package_name)
        module_path = '{}.py'.format('/'.join(path))
        module_name = path[-1]
        path = '/'.join(path[:-1])
        if not os.path.exists(path):
            os.makedirs(path)
        open(module_path, 'w').write(
            RELATION_TEMPLATE.format(
                package_name=package_name,
                class_name=camel_case(module_name), fqtn=fqtn))
    for root, dirs, files in os.walk(package_name):
        all_ = (
            [dir for dir in dirs if dir != '__pycache__'] +
            [file.replace('.py', '')
             for file in files
             if re.findall('.py$', file) and
             file != '__init__.py' and
             file != '__pycache__']
        )
        open('{}/__init__.py'.format(root), 'w').write(
            '__all__ = {}\n'.format(all_))

if __name__ == '__main__':
    main()
