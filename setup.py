#-*- coding: utf-8 -*-

import os
import codecs
from setuptools import setup

def read(name):
    return codecs.open(
        os.path.join(os.path.dirname(__file__), name), "r", "utf-8").read()

setup(
    name='half_orm',
    version='0.3.1',
    description="A simple Python ORM only dealing with the DML part of SQL.",
    long_description=read('README.md'),
    keywords='',
    author='Joël Maïzi',
    author_email='joel.maizi@collorg.org',
    url='https://github.com/collorg/half_orm',
    license='GPL',
    packages=['half_orm', 'half_orm/hop'],
    package_data={'half_orm': [
        'hop/templates/*',
        'hop/db_patch_system/*']},
    install_requires=[
        'psycopg2-binary',
        'PyYAML',
        'pydash',
        'GitPython'],
    entry_points={
        'console_scripts': [
            'hop=half_orm.hop:main',
        ],
    },
)
