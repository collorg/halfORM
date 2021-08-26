import os

version_file = os.path.join(os.path.dirname(__file__), 'version.txt')
VERSION = open(version_file).read().strip()