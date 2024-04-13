"""Package for PostgreSQL {dbname} database.
You can edit the following parameters:
- version
- author
- author_email
- license
- keywords
"""

from setuptools import setup, find_packages
from codecs import open
from os import path
import re
import half_orm

PWD = path.abspath(path.dirname(__file__))

def get_long_description():
    """
    Return the README.
    """
    with open("README.md", encoding="utf8") as f:
        return f.read()

def get_version(package):
    """
    Return package version as listed in `__version__` in `init.py`.
    """
    with open(path.join(package, "version.txt")) as f:
        return f.read()


package_name='{package_name}'

setup(
    name=package_name,

    version=get_version(package_name),

    description='Package for {dbname} PG',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',
    url='',

    author='',
    author_email='',
    license='',

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
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],

    keywords='',

    packages=find_packages(exclude=['contrib', 'docs', 'tests', 'patches', 'svg']),

    install_requires=[
        'half_orm=={half_orm_version}'
    ],

)
