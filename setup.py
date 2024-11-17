#-*- coding: utf-8 -*-

import os
import codecs
from setuptools import setup

def read(name):
    file_name = os.path.join(os.path.abspath(os.path.dirname(__file__)), name)
    return codecs.open(file_name, "r", "utf-8").read()

def package_files(*directories):
    paths = set()
    for directory in directories:
        for (path, dirs, filenames) in os.walk(directory):
            dirs[:] = [dir for dir in dirs if dir not in {'hop_test', '.git', '__pycache__'}]
            for filename in filenames:
                paths.add(os.path.join('..', path, filename))
    return list(paths)

extra_files = package_files('half_orm/packager/templates', 'half_orm/packager/patches')

setup(
    name='half_orm',
    version=read('half_orm/version.txt').strip(),
    description="A simple PostgreSQL to Python mapper.",
    long_description=read('README.md'),
    keywords='',
    author='Joël Maïzi',
    author_email='joel.maizi@collorg.org',
    url='https://github.com/collorg/halfORM',
    license='GPLv3',
    packages=['half_orm', 'half_orm/packager'],
    install_requires=[
        'psycopg2-binary',
        'click',
        'GitPython'],
    package_data={'half_orm': ['version.txt', 'packager/version.txt'], '': extra_files},
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Database :: Front-Ends',
        'Topic :: Software Development :: Libraries :: Application Frameworks',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13'
    ],
    entry_points={
        'console_scripts': [
            'hop=half_orm.packager.hop:main',
        ],
    },
    long_description_content_type = "text/markdown"

)
