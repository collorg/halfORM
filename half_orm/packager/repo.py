"""The pkg_conf module provides the Repo class.
"""

import os
import sys
from configparser import ConfigParser
from typing import Optional
import half_orm
from half_orm import utils
from half_orm.packager.database import Database
from half_orm.packager.hgit import HGit
from half_orm.packager import modules
from half_orm.packager.patch import Patch
from half_orm.packager.changelog import Changelog

class Config:
    """
    """
    __name: Optional[str] = None
    __git_origin: str = ''
    __devel: bool = False
    __hop_version: Optional[str] = None
    def __init__(self, base_dir, **kwargs):
        Config.__file = os.path.join(base_dir, '.hop', 'config')
        self.__name = kwargs.get('name')
        self.__devel = kwargs.get('devel', False)
        if os.path.exists(self.__file):
            sys.path.insert(0, base_dir)
            self.read()

    def read(self):
        "Sets __name and __hop_version"
        config = ConfigParser()
        config.read(self.__file)
        self.__name = config['halfORM']['package_name']
        self.__hop_version = config['halfORM'].get('hop_version', '')
        self.__git_origin = config['halfORM'].get('git_origin', '')
        self.__devel = config['halfORM'].getboolean('devel', False)

    def write(self):
        "Helper: write file in utf8"
        config = ConfigParser()
        self.__hop_version = utils.hop_version()
        data = {
            'config_file': self.__name,
            'package_name': self.__name,
            'hop_version': self.__hop_version,
            'git_origin': self.__git_origin,
            'devel': self.__devel
        }
        config['halfORM'] = data
        with open(Config.__file, 'w', encoding='utf-8') as configfile:
            config.write(configfile)

    @property
    def name(self):
        return self.__name
    @name.setter
    def name(self, name):
        self.__name = name

    @property
    def git_origin(self):
        return self.__git_origin
    @git_origin.setter
    def git_origin(self, origin):
        "Sets the git origin and register it in .hop/config"
        self.__git_origin = origin
        self.write()

    @property
    def hop_version(self):
        return self.__hop_version
    @hop_version.setter
    def hop_version(self, version):
        self.__hop_version = version
        self.write()

    @property
    def devel(self):
        return self.__devel
    @devel.setter
    def devel(self, devel):
        self.__devel = devel

class Repo:
    """Reads and writes the hop repo conf file.
    """
    __new = False
    __checked: bool = False
    __base_dir: Optional[str] = None
    __config: Optional[Config] = None
    database: Optional[Database] = None
    hgit: Optional[HGit] = None
    def __init__(self):
        self.__check()

    @property
    def new(self):
        "Returns if the repo is being created or not."
        return Repo.__new

    @property
    def checked(self):
        "Returns if the Repo is OK."
        return self.__checked

    @property
    def production(self):
        "Returns the production status of the database"
        return self.database.production

    @property
    def model(self):
        "Returns the Model (halfORM) of the database"
        return self.database.model

    def __check(self):
        """Searches the hop configuration file for the package.
        This method is called when no hop config file is provided.
        Returns True if we are in a repo, False otherwise.
        """
        base_dir = os.path.abspath(os.path.curdir)
        while base_dir:
            if self.__set_base_dir(base_dir):
                self.database = Database(self)
                if self.devel:
                    self.hgit = HGit(self)
                    current_branch = self.hgit.branch
                    self.changelog = Changelog(self)
                    # only check if the branch is clean
                    if self.hgit.repos_is_clean():
                        self.hgit.check_rebase_hop_main(current_branch)
                self.__checked = True
            par_dir = os.path.split(base_dir)[0]
            if par_dir == base_dir:
                break
            base_dir = par_dir

    def __set_base_dir(self, base_dir):
        conf_file = os.path.join(base_dir, '.hop', 'config')
        if os.path.exists(conf_file):
            self.__base_dir = base_dir
            self.__config = Config(base_dir)
            return True
        return False

    @property
    def base_dir(self):
        "Returns the base dir of the repository"
        return self.__base_dir

    @property
    def name(self):
        "Returns the name of the package"
        return self.__config and self.__config.name or None

    @property
    def git_origin(self):
        "Returns the git origin registered in .hop/config"
        return self.__config.git_origin
    @git_origin.setter
    def git_origin(self, origin):
        self.__config.git_origin = origin

    def __hop_version_mismatch(self):
        """Returns a boolean indicating if current hop version is different from
        the last hop version used with this repository.
        """
        return utils.hop_version() != self.__config.hop_version

    @property
    def devel(self):
        return self.__config.devel

    @property
    def state(self):
        "Returns the state (str) of the repository."
        res = [f'hop version: {utils.Color.bold(utils.hop_version())}']
        res += [f'half-orm version: {utils.Color.bold(half_orm.__version__)}\n']
        if self.__config:
            hop_version = utils.Color.red(self.__config.hop_version) if \
                self.__hop_version_mismatch() else \
                utils.Color.green(self.__config.hop_version)
            res += [
                '[Hop repository]',
                f'- base directory: {self.__base_dir}',
                f'- package name: {self.__config.name}',
                f'- hop version: {hop_version}'
            ]
            res.append(self.database.state)
            res.append(str(self.hgit))
            res.append(Patch(self).state)
        return '\n'.join(res)

    def init(self, package_name, devel):
        "Create a new hop repository"
        Repo.__new = True
        cur_dir = os.path.abspath(os.path.curdir)
        self.__base_dir = os.path.join(cur_dir, package_name)
        self.__config = Config(self.__base_dir, name=package_name, devel=devel)
        self.database = Database(self, get_release=False).init(self.__config.name)
        print(f"Installing new hop repo in {self.__base_dir}.")

        if not os.path.exists(self.__base_dir):
            os.makedirs(self.__base_dir)
        else:
            utils.error(f"ERROR! The path '{self.__base_dir}' already exists!\n", exit_code=1)
        readme = utils.read(os.path.join(utils.TEMPLATE_DIRS, 'README'))
        setup_template = utils.read(os.path.join(utils.TEMPLATE_DIRS, 'setup.py'))
        git_ignore = utils.read(os.path.join(utils.TEMPLATE_DIRS, '.gitignore'))
        pipfile = utils.read(os.path.join(utils.TEMPLATE_DIRS, 'Pipfile'))

        setup = setup_template.format(
                dbname=self.__config.name,
                package_name=self.__config.name,
                half_orm_version=half_orm.__version__)
        utils.write(os.path.join(self.__base_dir, 'setup.py'), setup)

        pipfile = pipfile.format(
                half_orm_version=half_orm.__version__,
                hop_version=utils.hop_version())
        utils.write(os.path.join(self.__base_dir, 'Pipfile'), pipfile)

        os.mkdir(os.path.join(self.__base_dir, '.hop'))
        self.__config.write()
        modules.generate(self)

        readme = readme.format(
            hop_version=utils.hop_version(), dbname=self.__config.name, package_name=self.__config.name)
        utils.write(os.path.join(self.__base_dir, 'README.md'), readme)
        utils.write(os.path.join(self.__base_dir, '.gitignore'), git_ignore)
        self.hgit = HGit().init(self.__base_dir)

        print(f"\nThe hop project '{self.__config.name}' has been created.")
        print(self.state)

    def sync_package(self):
        Patch(self).sync_package()

    def upgrade_prod(self):
        "Upgrade (production)"
        Patch(self).upgrade_prod()

    def restore(self, release):
        "Restore package and database to release (production/devel)"
        Patch(self).restore(release)

    def prepare_release(self, level, message=None):
        "Prepare a new release (devel)"
        Patch(self).prep_release(level, message)

    def apply_release(self):
        "Apply the current release (devel)"
        Patch(self).apply(self.hgit.current_release, force=True)

    def undo_release(self, database_only=False):
        "Undo the current release (devel)"
        Patch(self).undo(database_only=database_only)

    def commit_release(self, push):
        "Release a 'release' (devel)"
        Patch(self).release(push)
