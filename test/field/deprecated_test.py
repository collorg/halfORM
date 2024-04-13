import os
from unittest import TestCase

from ..init import halftest

ERR_MSG = """WARNING! Field._set method is deprecated. Use Field.set instead.
It will be remove in 1.0 version.
"""

def test_deprecated(capsys):
    "_set is deprecated"
    pers = halftest.Person()
    pers.last_name._set('aabc')
    _, err = capsys.readouterr()
    TestCase().assertEqual(err, ERR_MSG)
