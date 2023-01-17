#!/usr/bin/env bash

set -ex

cat $CI_PROJECT_DIR/.config/hop_test
perl -spi -e 's=True=False=' $CI_PROJECT_DIR/.config/hop_test

rm -rf hop_test
set +e
dropdb hop_test
set -e

yes | hop new hop_test

cd hop_test

tree -a -I .git .

rm -rf /tmp/hop_test.git
git init --bare /tmp/hop_test.git
git remote add origin /tmp/hop_test.git
git push -u origin hop_main

git status

hop prepare-release -m "First patch release" << EOF
patch
EOF
echo 'create table first ( a text primary key )' > Patches/0/0/1/a.sql
hop apply-release
git add .
git commit -m "First table"
hop commit-release

hop prepare-release -l patch -m "Second patch release"

echo 'create table a ( a text primary key )' > Patches/0/0/2/a.sql
echo 'print("I am a script without x permission...")' > Patches/0/0/2/a.py

hop apply-release

tree .

hop

yes | hop apply-release

hop apply-release

git add .
git commit -m "(wip) First"
git status

echo 'create table a ( a text primary key, bla text )' > Patches/0/0/2/a.sql

hop undo-release

hop apply-release
git diff hop_test/public/a.py

git status

set +e
# should commit before release
hop commit-release -m "First release"
if [ $? = 0 ]; then exit 1; fi
set -e

git add .
git commit -m "(wip) ajout de a.bla"

touch dirty
set +e
# git repo must be clean
hop commit-release
if [ $? = 0 ]; then exit 1; fi
set -e
rm dirty

echo '        verybad' >> hop_test/public/a.py
git add .
git commit -m "(bad)"
set +e
# git repo must be clean
hop commit-release
if [ $? = 0 ]; then exit 1; fi
set -e
git reset HEAD~ --hard

hop commit-release --push

git status

hop

hop prepare-release -l minor -m "First minor patch"

echo 'create table b ( b text primary key, a text references a )' > Patches/0/1/0/b.sql

hop apply-release

tree

# git diff
git status

git add .
git commit -m "(wip) Second"

cat > hop_test/public/b.py << EOF
# pylint: disable=wrong-import-order, invalid-name, attribute-defined-outside-init

"""The module hop_test.public.b povides the B class.

WARNING!

This file is part of the hop_test package. It has been generated by the
command hop. To keep it in sync with your database structure, just rerun
hop update.

More information on the half_orm library on https://github.com/collorg/halfORM.

DO NOT REMOVE OR MODIFY THE LINES BEGINING WITH:
#>>> PLACE YOUR CODE BELOW...
#<<< PLACE YOUR CODE ABOVE...

MAKE SURE YOUR CODE GOES BETWEEN THESE LINES OR AT THE END OF THE FILE.
hop ONLY PRESERVES THE CODE BETWEEN THESE MARKS WHEN IT IS RUN.
"""

from hop_test.db_connector import base_relation_class

#>>> PLACE YOUR CODE BELLOW THIS LINE. DO NOT REMOVE THIS LINE!
import datetime
#<<< PLACE YOUR CODE ABOVE THIS LINE. DO NOT REMOVE THIS LINE!

__RCLS = base_relation_class('public.b')

class B(__RCLS):
    """
    __RCLS: <class 'half_orm.model.Table_Hop_testPublicB'>
    This class allows you to manipulate the data in the PG relation:
    TABLE: "hop_test":"public"."b"
    FIELDS:
    - b: (text) NOT NULL
    - a: (text)

    PRIMARY KEY (b)
    FOREIGN KEY:
    - b_a_fkey: ("a")
     ↳ "hop_test":"public"."a"(a)

    To use the foreign keys as direct attributes of the class, copy/paste the Fkeys bellow in
    your code as a class attribute and replace the empty string(s) key(s) with the alias you
    want to use. The aliases must be unique and different from any of the column names. Empty
    string keys are ignored.

    Fkeys = {
        '': 'b_a_fkey',
    }
    """
    #>>> PLACE YOUR CODE BELLOW THIS LINE. DO NOT REMOVE THIS LINE!
    Fkeys = {
        'a_fk': 'b_a_fkey',
    }
    #<<< PLACE YOUR CODE ABOVE THIS LINE. DO NOT REMOVE THIS LINE!
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        #>>> PLACE YOUR CODE BELLOW THIS LINE. DO NOT REMOVE THIS LINE!
EOF

git add .
git commit -m "(b) with Fkeys"

mkdir hop_test/Api
touch hop_test/Api/__init__.py
mkdir hop_test/Api/coucou
echo 'print ("coucou")' > hop_test/Api/coucou/__init__.py

git add .
git commit -m "Add API"

hop commit-release

git status
git push
git tag

hop prepare-release -l major -m major
git checkout hop_main
hop prepare-release -l minor -m minor
git checkout hop_main
hop prepare-release -l patch -m patch
git checkout hop_main

set +e
hop prepare-release -l minor -m coucou
if [ $? = 0 ]; then exit 1; fi
set -e

hop

git checkout hop_0.2.0

hop

set +e
hop commit-release
if [ $? = 0 ]; then exit 1; fi
set -e

git checkout hop_0.1.1
hop apply-release
touch Patches/0/1/1/coucou
git add .
git commit -m "[WIP] 0.1.1 test"
hop apply-release
hop commit-release

cat > TODO << EOF
something
EOF
git add TODO
git commit -m "Add todo to check rebase on apply-release"

git checkout hop_0.2.0
hop apply-release
touch Patches/0/2/0/coucou
git add .
git commit -m "[WIP] 0.2.0 test"
hop apply-release
hop commit-release

hop prepare-release -l patch -m "0.2.1..."
hop apply-release
touch Patches/0/2/1/coucou
git add .
git commit -m "[0.2.1] coucou"
hop commit-release

git checkout hop_1.0.0
hop apply-release
touch Patches/1/0/0/coucou
git add .
git commit -m "[WIP] 1.0.0 test"
hop apply-release
hop commit-release

git push

echo 'APPLY PATCH IN PRODUCTION'
perl -spi -e 's=False=True=' $CI_PROJECT_DIR/.config/hop_test
hop
hop restore 0.1.1
hop
hop upgrade
perl -spi -e 's=True=False=' $CI_PROJECT_DIR/.config/hop_test
