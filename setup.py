#-*- coding: utf-8 -*-

import os
import codecs
from setuptools import setup

def read(name):
    file_name = os.path.join(os.path.abspath(os.path.dirname(__file__)), name)
    return codecs.open(file_name, "r", "utf-8").read()

setup(
    name='half_orm',
    version=read('half_orm/version.txt').strip(),
    description="A simple PostgreSQL-Python relation-object mapper.",
    long_description=read('README.md'),
    keywords='',
    author='Joël Maïzi',
    author_email='joel.maizi@collorg.org',
    url='https://github.com/collorg/halfORM',
    license='GNU General Public License v3 (GPLv3)',
    packages=['half_orm'],
    install_requires=[
        'psycopg2-binary',
        'PyYAML'],
    package_data={'half_orm': ['version.txt']},
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
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    long_description_content_type = "text/markdown"

)
