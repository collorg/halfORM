"""The changelog module

Manages the CHANGELOG file. The file contains the log of the patches (released) and in preparation.

A line is of the form:
<hop version>\t<release number>\t<commit>\t<previous commit>

* hop version allows to check that the good hop version is used to apply the patch in production
* release number is an ordered list of release number
* commit is the git sha1 corresponding to the release of the patch. If empty, the patch is in
  preparation.
* previous commit is the last commit on hop_main before the rebase of hop_<release>

"""

import os

from half_orm.packager import utils

class Changelog:
    "The Changelog class..."
    __log_list = []
    __log_dict = {}
    __releases = []
    def __init__(self, repo):
        self.__repo = repo
        self.__file = os.path.join(self.__repo.base_dir, '.hop', 'CHANGELOG')
        if not os.path.exists(self.__file):
            utils.write(
                self.__file,
                f'{utils.hop_version()}\t{self.__repo.database.last_release_s}\tInitial\t\n')
        self.__seq()

    def __seq(self):
        self.__log_list = [elt.strip('\n').split('\t') for elt in utils.readlines(self.__file)]
        self.__log_dict = {elt[1]: elt for elt in self.__log_list}
        self.__releases = list(self.__log_dict.keys())

    def new_release(self, release):
        """Update with the release the .hop/CHANGELOG file"""
        releases = self.__releases
        releases.append(release)
        releases.sort()
        utils.write(self.__file, '')
        for elt in releases:
            rel = self.__log_dict.get(elt)
            if rel:
                utils.write(self.__file, f'{rel[0]}\t{rel[1]}\t{rel[2]}\t{rel[3]}\n', mode='a+')
            else:
                utils.write(self.__file, f'{utils.hop_version()}\t{release}\t\t\n', mode='a+')
        self.__seq()

    def update_release(self, release, commit, previous_commit):
        "Add the commit sha1 to the release in the .hop/CHANGELOG file"
        out = []
        previous = self.previous(release)
        for line in utils.readlines(self.__file):
            if line and line.split()[1] not in {release, previous}:
                out.append(line)
            elif line.split()[1] == previous:
                elt = line.split()
                out.append(f'{elt[0]}\t{elt[1]}\t{elt[2]}\t{previous_commit}\n')
            else:
                out.append(f'{utils.hop_version()}\t{release}\t{commit}\t\n')
        utils.write(self.__file, ''.join(out))
        self.__repo.hgit.add(self.__file)
        # self.__repo.hgit.commit('-m', f'[hop][{release}] CHANGELOG')
        self.__seq()

    def previous(self, release):
        "Return previous release of release."
        index_of_release = self.__releases.index(release)
        return self.__releases[index_of_release - 1]

    @property
    def file(self):
        "Return the name of the changelog file"
        return self.__file

    @property
    def last_release(self):
        "Return the sequence"
        releases = [elt[1] for elt in self.__log_list if elt[2]]
        return releases[-1]

    @property
    def releases_in_dev(self):
        "Returns the list of patches in dev (not released)"
        return [elt[1] for elt in self.__log_list if not elt[2]]

    @property
    def releases_to_apply_in_prod(self):
        "Returns the list of releases to apply in production"
        current = self.__repo.database.last_release_s
        releases_to_apply = []
        to_apply = False
        for elt in self.__log_list:
            if elt[1] == current:
                # we're here
                to_apply = True
                continue
            if to_apply and elt[2]:
                releases_to_apply.append(elt[1])
        return releases_to_apply
