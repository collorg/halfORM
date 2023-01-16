#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generates/Patches/Synchronizes a hop Python package with a PostgreSQL database
using the `hop` command.

Initiate a new project and repository with the `hop new <project_name>` command.
The <project_name> directory should not exist when using this command.

In the <project name> directory generated, the hop command helps you patch your
model, keep your Python synced with the PostgreSQL model, test your Python code and
deal with CI.

TODO:
On the 'devel' or any private branch hop applies patches if any, runs tests.
On the 'main' or 'master' branch, hop checks that your git repo is in sync with
the remote origin, synchronizes with devel branch if needed and tags your git
history with the last release applied.
"""

import sys

import click

from half_orm.packager.repo import Repo
from half_orm.packager import utils

class Hop:
    "Sets the options available to the hop command"
    __available_cmds = []
    __command = None
    def __init__(self):
        self.__repo: Repo = Repo()
        if not self.repo_checked:
            Hop.__available_cmds = ['new']
        else:
            if not self.__repo.production:
                if self.__repo.hgit.branch == 'hop_main':
                    Hop.__available_cmds = ['prepare-release']
                elif self.__repo.hgit.is_hop_patch_branch:
                    Hop.__available_cmds = ['test-release', 'undo-release', 'commit-release']
            else:
                Hop.__available_cmds = ['upgrade', 'restore']

    @property
    def repo_checked(self):
        "Returns wether we are in a repo or not."
        return self.__repo.checked

    @property
    def model(self):
        "Returns the model (half_orm.model.Model) associated to the repo."
        return self.__repo.model

    @property
    def state(self):
        "Returns the state of the repo."
        return self.__repo.state

    @property
    def command(self):
        "The command invoked (click)"
        return self.__command

    def add_commands(self, click_main):
        "Adds the commands to the main click group."
        @click.command()
        @click.argument('package_name')
        @click.option('-d', '--devel', is_flag=True, help="Development mode")
        def new(package_name, devel=False):
            """ Creates a new hop project named <package_name>.
            """
            self.__repo.new(package_name)


        @click.command()
        @click.option(
            '-l', '--level',
            type=click.Choice(['patch', 'minor', 'major']), help="Release level.")
        @click.option('-m', '--message', type=str, help="The commit message")
        def prepare_release(level, message=None):
            """ Prepares the next release.
            """
            self.__command = 'prepare-release'
            self.__repo.prepare_release(level, message)
            sys.exit()

        @click.command()
        def test_release():
            """Apply the current release.
            """
            self.__command = 'test-release'
            self.__repo.test_release()

        @click.command()
        @click.option(
            '-d', '--database-only', is_flag=True,
            help='Restore the database to the previous release.')
        def undo_release(database_only):
            """Undo the last release.
            """
            self.__command = 'undo-release'
            self.__repo.undo_release(database_only)

        @click.command()
        # @click.option('-d', '--dry-run', is_flag=True, help='Do nothing')
        # @click.option('-l', '--loop', is_flag=True, help='Run every patches to apply')
        def upgrade():
            """Apply one or many patches.

            switches to hop_main, pulls should check the tags
            """
            self.__command = 'upgrade_prod'
            self.__repo.upgrade_prod()

        @click.command()
        @click.argument('release')
        def restore(release):
            "Restore to release"
            self.__repo.restore(release)

        @click.command()
        @click.option('-p', '--push', is_flag=True, help='Push git repo to origin')
        def commit_release(push=False):
            self.__repo.commit_release(push)

        cmds = {
            'new': new,
            'prepare-release': prepare_release,
            'test-release': test_release,
            'undo-release': undo_release,
            'commit-release': commit_release,
            'upgrade': upgrade,
            'restore': restore
        }

        for cmd in self.__available_cmds:
            click_main.add_command(cmds[cmd])


hop = Hop()

@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """
    Generates/Synchronises/Patches a python package from a PostgreSQL database
    """
    if hop.repo_checked and ctx.invoked_subcommand is None:
        click.echo(hop.state)
    elif not hop.repo_checked and ctx.invoked_subcommand != 'new':
        utils.error(
            "You're not in a hop repository.\n"
            "Try `hop new <package name>` or change directory.\n", exit_code=1)

hop.add_commands(main)

if __name__ == '__main__':
    main({})
