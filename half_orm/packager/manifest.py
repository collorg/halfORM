"""Manages the MANIFEST.json
"""

import json
import os

from half_orm.packager import utils

class Manifest:
    "Manages the manifest of a release"
    def __init__(self, path):
        self.__hop_version = None
        self.__changelog_msg = None
        self.__file = os.path.join(path, 'MANIFEST.json')
        if os.path.exists(self.__file):
            manifest = utils.read(self.__file)
            data = json.loads(manifest)
            self.__hop_version = data['hop_version']
            self.__changelog_msg = data['changelog_msg']

    @property
    def changelog_msg(self):
        "Returns the changelog msg"
        return self.__changelog_msg
    @changelog_msg.setter
    def changelog_msg(self, msg):
        self.__changelog_msg = msg

    @property
    def hop_version(self):
        "Returns the version of hop used to create this release"
        return self.__hop_version
    @hop_version.setter
    def hop_version(self, release):
        self.__hop_version = release

    def write(self):
        "Writes the manifest"
        with open(self.__file, 'w', encoding='utf-8') as manifest:
            manifest.write(json.dumps({
                'hop_version': self.__hop_version,
                'changelog_msg': self.__changelog_msg
            }))
