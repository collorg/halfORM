#!/usr/bin/env python3

import os
import sys
from halfORM.model import Model

path = os.path.dirname(__file__)

README = """
Create the database halftest First:
- psql template1 -f {}/sql/halftest.sql
This command will create:
- a user halftest.
  When prompted for the password type: halftest
- a database halftest

To drop halftest database and user when you're done with the tests:
- dropdb halftest; dropuser halftest
"""

try:
    halftest = Model('halftest', path)
except Exception as err:
    sys.stderr.write('{}\n'.format(err))
    sys.stderr.write(README.format(path))
    sys.exit(1)
    
