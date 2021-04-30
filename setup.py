#-*- coding: utf-8 -*-

import sys
import os
import codecs
from setuptools import setup

def read(name):
    return codecs.open(
        os.path.join(os.path.dirname(__file__), name), "r", "utf-8").read()

setup(
    name='half_orm',
    version='0.3.1',
    description="A simple ORM in Python only dealing with the DML part of SQL.",
    long_description=read('README.md'),
    keywords='',
    author='Joël Maïzi',
    author_email='joel.maizi@collorg.org',
    url='https://github.com/collorg/half_orm',
    license='GPL',
    packages=['half_orm'],
    package_data={'half_orm': [
        'halfORM_templates/*',
        'halfORM_db_patch_system/*']},
    install_requires=['psycopg2-binary', 'PyYAML'],
    entry_points={
        'console_scripts': [
            'hop=half_orm.hop:main',
        ],
    },
)
