"""Provides the DbConn class.
"""

import os
import subprocess
import sys

from getpass import getpass
from configparser import ConfigParser

from half_orm.model import CONF_DIR
from half_orm import utils

CONF_NOT_FOUND = '''
The configuration file {} is missing.
You must create it before proceeding.

'''

class DbConn:
    """Handles the connection parameters to the database.
    Provides the execute_pg_command."""
    __conf_dir = CONF_DIR # HALFORM_CONF_DIR
    def __init__(self, name):
        self.__name = name
        self.__user = None
        self.__password = None
        self.__host = None
        self.__port = None
        self.__production = None
        if name:
            self.__connection_file = os.path.join(self.__conf_dir, self.__name)
            if not os.path.exists(self.__connection_file):
                utils.error(CONF_NOT_FOUND.format(self.__connection_file), 1)
            self.__init()

    @property
    def production(self):
        "prod"
        return self.__production

    def __init(self):
        "Reads the config file and sets the connection parameters"
        config = ConfigParser()
        config.read([self.__connection_file])

        self.__name = config.get('database', 'name')

        self.__user = config.get('database', 'user', fallback=None)
        self.__password = config.get('database', 'password', fallback=None)
        self.__host = config.get('database', 'host', fallback=None)
        self.__port = config.get('database', 'port', fallback=None)

        self.__production = config.getboolean('database', 'production', fallback=False)

    @property
    def host(self):
        "Returns host name"
        return self.__host
    @property
    def port(self):
        "Returns port"
        return self.__port
    @property
    def user(self):
        "Returns user"
        return self.__user

    def set_params(self, name):
        """Asks for the connection parameters.
        """
        self.__name = name
        if not os.access(self.__conf_dir, os.W_OK):
            sys.stderr.write(f"You don't have write access to {self.__conf_dir}.\n")
            if self.__conf_dir == '/etc/half_orm': # only on linux
                utils.error(
                    "Set the HALFORM_CONF_DIR environment variable if you want to use a\n"
                    "different directory.\n", exit_code=1)
        print(f'Connection parameters to the database {self.__name}:')
        self.__user = os.environ['USER']
        self.__user = input(f'. user ({self.__user}): ') or self.__user
        self.__password = getpass('. password: ')
        if self.__password == '' and \
                (input(
                    '. is it an ident login with a local account? [Y/n] ') or 'Y').upper() == 'Y':
            self.__host = self.__port = ''
        else:
            self.__host = input('. host (localhost): ') or 'localhost'
            self.__port = input('. port (5432): ') or 5432

        self.__production = input('Production (False): ') or False

        self.__write_config()

        return self

    def __write_config(self):
        "Helper: write file in utf8"
        self.__connection_file = os.path.join(self.__conf_dir, self.__name)
        config = ConfigParser()
        config['database'] = {
            'name': self.__name,
            'user': self.__user,
            'password': self.__password,
            'host': self.__host,
            'port': self.__port,
            'production': self.__production
        }
        with open(self.__connection_file, 'w', encoding='utf-8') as configfile:
            config.write(configfile)

    def execute_pg_command(self, cmd, *args, **kwargs):
        """Helper. Executes a postgresql
        """
        if not kwargs.get('stdout'):
            kwargs['stdout'] = subprocess.DEVNULL
        cmd_list = [cmd]
        env = os.environ.copy()
        password = self.__password
        if password:
            env['PGPASSWORD'] = password
        if self.__user:
            cmd_list += ['-U', self.__user]
        if self.__port:
            cmd_list += ['-p', self.__port]
        if self.__host:
            cmd_list += ['-h', self.__host]
        cmd_list.append(self.__name)
        if args:
            cmd_list += args
        try:
            subprocess.run(
                cmd_list, env=env, shell=False, check=True,
                **kwargs)
        except subprocess.CalledProcessError as err:
            utils.error(f'{err.stderr} with user: {self.__user}, host: {self.__host}, port: {self.__port}\n', exit_code=err.returncode)
