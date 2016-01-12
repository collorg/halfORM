#-*- coding: utf-8 -*-

import sys
import os
import codecs
from setuptools import setup

def read(name):
    return codecs.open(
        os.path.join(os.path.dirname(__file__), name), "r", "utf-8").read()

setup(
    name='halfORM',
    version='0.0.1',
    description="A simple ORM in Python only dealing with the DML part of SQL.",
    long_description=read('README.md'),
    keywords='',
    author='Joël Maïzi',
    author_email='joel.maizi@collorg.org',
    url='https://github.com/collorg/halfORM',
    license='GPL',
    packages=['halfORM'],
    install_requires=['psycopg2>=2.6.1'],
)
