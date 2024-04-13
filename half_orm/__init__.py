"""half_orm package
"""

import os

version_file = os.path.join(os.path.dirname(__file__), 'version.txt')
with open(version_file) as version:
  __version__ = version.read().strip()
  VERSION = version # Backward compatibility. Use __version__ instead.
