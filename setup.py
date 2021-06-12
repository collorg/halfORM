#-*- coding: utf-8 -*-

import os
import codecs
from setuptools import setup

def read(name):
    return codecs.open(
        os.path.join(os.path.dirname(__file__), name), "r", "utf-8").read()

setup(
    name='half_orm',
    version='0.4.4',
    description="A simple Python ORM only dealing with the DML part of SQL.",
    long_description=read('README.md'),
    keywords='',
    author='Joël Maïzi',
    author_email='joel.maizi@collorg.org',
    url='https://github.com/collorg/half_orm',
    license='GPLv3',
    packages=['half_orm', 'half_orm/hop'],
    package_data={'half_orm': [
        'hop/templates/*',
        'hop/db_patch_system/*']},
    install_requires=[
        'psycopg2-binary',
        'PyYAML',
        'pydash',
        'GitPython',
        'click'],
    entry_points={
        'console_scripts': [
            'hop=half_orm.hop:main',
        ],
    },
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
        'License :: OSI Approved :: GPLv3 License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],

)
