#-*- coding: utf-8 -*-

import os
from setuptools import setup

def read(name):
    return open(os.path.join(os.path.dirname(__file__), name)).read()

setup(
    name='halfORM',
    version='0.0.1',
    description=" A simple ORM in Python only dealing with DML part of SQL.",
    long_description=read('README.rst'),
    keywords='',
    author='Joël Maïzi',
    author_email='joel.maizi@collorg.org',
    url='https://github.com/collorg/halfORM',
    license='GPL',
    packages=['halfORM'],
    install_requires=['psycopg2>=2.6.1'],
)
