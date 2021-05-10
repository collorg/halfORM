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

PWD = path.abspath(path.dirname(__file__))

with open(path.join(PWD, 'README.md'), encoding='utf-8') as f:
    LONG_DESCRIPTION = f.read()

setup(
    name='{package_name}',

    version='0.0.0',

    description='Package for {dbname} PG',
    long_description=LONG_DESCRIPTION,

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
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],

    keywords='',

    packages=find_packages(exclude=['contrib', 'docs', 'tests', 'patches', 'svg']),

    install_requires=['half_orm'],

)
