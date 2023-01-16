"""The pkg_conf module provides the Repo class.
"""

import os
from configparser import ConfigParser
import half_orm
from half_orm.packager import utils
from half_orm.packager.database import Database
from half_orm.packager.hgit import HGit
from half_orm.packager import modules
from half_orm.packager.patch import Patch
from half_orm.packager.changelog import Changelog

class Repo:
    """Reads and writes the hop repo conf file.
    """
    __checked: bool = False
    __self_hop_version: str = None
    __base_dir: str = None
    __name: str = None
    __database: Database = Database()
    __hgit: HGit = None
    __conf_file: str = None
    def __init__(self):
        self.__check()

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
                self.database = Database(self.__name)
                self.hgit = HGit(self)
                self.changelog = Changelog(self)
                self.__checked = True
            par_dir = os.path.split(base_dir)[0]
            if par_dir == base_dir:
                break
            base_dir = par_dir

    def __set_base_dir(self, base_dir):
        conf_file = os.path.join(base_dir, '.hop', 'config')
        if os.path.exists(conf_file):
            self.__base_dir = base_dir
            self.__conf_file: str = conf_file
            self.__load_config()
            return True
        return False

    @property
    def base_dir(self):
        "Returns the base dir of the repository"
        return self.__base_dir

    @property
    def name(self):
        "Returns the name of the package"
        return self.__name
    @name.setter
    def name(self, name):
        self.__name = name

    def __load_config(self):
        "Sets __name and __hop_version"
        config = ConfigParser()
        config.read(self.__conf_file)
        self.__name = config['halfORM']['package_name']
        self.__self_hop_version = config['halfORM'].get('hop_version')

    def __write_config(self):
        "Helper: write file in utf8"
        Repo.__conf_file = os.path.join(self.__base_dir, '.hop', 'config')
        config = ConfigParser()
        config['halfORM'] = {
            'config_file': self.__name,
            'package_name': self.__name,
            'hop_version': utils.hop_version()
        }
        with open(Repo.__conf_file, 'w', encoding='utf-8') as configfile:
            config.write(configfile)

    def __hop_version_mismatch(self):
        """Returns a boolean indicating if current hop version is different from
        the last hop version used with this repository.
        """
        return utils.hop_version() != self.__self_hop_version

    @property
    def state(self):
        "Returns the state (str) of the repository."
        res = [f'Half-ORM packager: {utils.hop_version()}\n']
        hop_version = utils.Color.red(self.__self_hop_version) if \
            self.__hop_version_mismatch() else \
            utils.Color.green(self.__self_hop_version)
        res += [
            '[Hop repository]',
            f'- base directory: {self.__base_dir}',
            f'- package name: {self.__name}',
            f'- hop version: {hop_version}'
        ]
        res.append(self.database.state)
        res.append(str(self.hgit))
        res.append(Patch(self).state)
        return '\n'.join(res)

    def new(self, package_name):
        "Create a new hop repository"
        self.__name = package_name
        self.__self_hop_version=utils.hop_version()
        cur_dir = os.path.abspath(os.path.curdir)
        self.__base_dir = os.path.join(cur_dir, package_name)
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
                dbname=self.__name,
                package_name=self.__name,
                half_orm_version=half_orm.VERSION)
        utils.write(os.path.join(self.__base_dir, 'setup.py'), setup)

        pipfile = pipfile.format(
                half_orm_version=half_orm.VERSION,
                hop_version=self.__self_hop_version)
        utils.write(os.path.join(self.__base_dir, 'Pipfile'), pipfile)

        os.mkdir(os.path.join(self.__base_dir, '.hop'))
        self.__write_config()
        self.__load_config()
        self.database = Database().init(self.__name)
        modules.generate(self)

        readme = readme.format(
            hop_version=self.__self_hop_version, dbname=self.__name, package_name=self.__name)
        utils.write(os.path.join(self.__base_dir, 'README.md'), readme)
        utils.write(os.path.join(self.__base_dir, '.gitignore'), git_ignore)
        self.hgit = HGit().init(self.__base_dir)

        print(f"\nThe hop project '{self.__name}' has been created.")
        print(self.state)


    def upgrade_prod(self):
        "Upgrade (production)"
        Patch(self).upgrade_prod()

    def restore(self, release):
        "Restore package and database to release (production/devel)"
        Patch(self).restore(release)

    def prepare_release(self, level, message=None):
        "Prepare a new release (devel)"
        Patch(self).prep_release(level, message)

    def test_release(self):
        "Apply the current release (devel)"
        Patch(self).apply(self.hgit.current_release, force=True)

    def undo_release(self, database_only=False):
        "Undo the current release (devel)"
        Patch(self).undo(database_only=database_only)

    def commit_release(self, push):
        "Release a 'release' (devel)"
        Patch(self).release(push)
