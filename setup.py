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
    version='0.1.0',
    description="A simple ORM in Python only dealing with the DML part of SQL.",
    long_description=read('README.md'),
    keywords='',
    author='Joël Maïzi',
    author_email='joel.maizi@collorg.org',
    url='https://github.com/collorg/half_orm',
    license='GPL',
    packages=['half_orm'],
    install_requires=['psycopg2>=2.6.1', 'PyYAML'],
    entry_points={
        'console_scripts': [
            'halfORM=half_orm.halfORM:main',
        ],
    },
)
