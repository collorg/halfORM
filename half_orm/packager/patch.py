"The patch module"

import json
import os
import subprocess
import sys

import pydash
import psycopg2

from half_orm.packager import utils
from half_orm.packager import modules
from half_orm.packager.changelog import Changelog

class Patch:
    "The Patch class..."
    __levels = ['patch', 'minor', 'major']

    def __init__(self, repo):
        self.__repo = repo
        self.__patches_base_dir = os.path.join(repo.base_dir, 'Patches')
        self.__changelog = Changelog(repo)
        if not os.path.exists(self.__patches_base_dir):
            os.makedirs(self.__patches_base_dir)

    @classmethod
    @property
    def levels(cls):
        "Returns the levels"
        return cls.__levels

    def previous(self, release):
        "Return .hop/CHANGELOG second to last line."
        return self.__changelog.previous(release)

    @property
    def __next_releases(self):
        db_last_release = self.__repo.database.last_release_s
        ch_last_release = self.__changelog.last_release
        if db_last_release != ch_last_release:
            utils.error(
                f'Last release mismatch between database {db_last_release}'
                f' and CHANGELOG {ch_last_release}!\n', 1)
        current = dict(self.__repo.database.last_release)
        releases_in_dev = self.__changelog.releases_in_dev
        n_rels = {}
        for level in self.__levels:
            n_rel = dict(current)
            n_rel[level] = current[level] + 1
            if level == 'major':
                n_rel['minor'] = n_rel['patch'] = 0
            if level == 'minor':
                n_rel['patch'] = 0
            next_release_s = f"{n_rel['major']}.{n_rel['minor']}.{n_rel['patch']}"
            n_rel['in_dev'] = ''
            if next_release_s in releases_in_dev:
                n_rel['in_dev'] = '(IN DEV)'
            n_rels[level] = n_rel
        return n_rels

    def prep_release(self, release_level, message=None):
        """Returns the next (major, minor, patch) tuple according to the release_level

        Args:
            release_level (str): one of ['patch', 'minor', 'major']
        """
        if str(self.__repo.hgit.branch) != 'hop_main':
            utils.error(
                'ERROR! Wrong branch. Please, switch to the hop_main branch before.\n', exit_code=1)
        next_releases = self.__next_releases
        if release_level is None:
            next_levels = '\n'.join(
                [f"""- {level}: {'{major}.{minor}.{patch} {in_dev}'.format(**next_releases[level])}"""
                for level in self.__levels])
            print(f'Next releases:\n{next_levels}')
            next_possible_releases = [elt for elt in self.__levels if not next_releases[elt]['in_dev']]
            release_level = input(f"Release level {next_possible_releases}? ")
            if not release_level in next_possible_releases:
                utils.error(f"Wrong release level ({release_level}).\n", exit_code=1)
        else:
            if next_releases[release_level]['in_dev']:
                utils.error(f'{release_level} is alredy in development!\n', 1)
        next_release = dict(self.__repo.database.last_release)
        next_release[release_level] = next_release[release_level] + 1
        if release_level == 'major':
            next_release['minor'] = next_release['patch'] = 0
        if release_level == 'minor':
            next_release['patch'] = 0
        new_release_s = '{major}.{minor}.{patch}'.format(**next_release)
        rel_branch = f'hop_{new_release_s}'
        if self.__repo.hgit.branch_exists(rel_branch):
            utils.error(f'{rel_branch} already exists!\n', 1)
        print(f'PREPARING: {new_release_s}')
        patch_path = os.path.join(
            'Patches',
            str(next_release['major']),
            str(next_release['minor']),
            str(next_release['patch']))
        if not os.path.exists(patch_path):
            changelog_msg = message or input('Message - (leave empty to abort): ')
            if not changelog_msg:
                print('Aborting')
                return
            os.makedirs(patch_path)
            with open(os.path.join(patch_path, 'MANIFEST.json'), 'w', encoding='utf-8') as manifest:
                manifest.write(json.dumps({
                    'hop_version': utils.hop_version(),
                    'changelog_msg': changelog_msg,
                }))
        self.__changelog.new_release(new_release_s)
        self.__repo.hgit.set_branch(new_release_s)
        print('You can now add your patch scripts (*.py, *.sql)'
            f'in {patch_path}. See Patches/README.')
        modules.generate(self.__repo)

    def __check_apply_or_re_apply(self):
        """Return True if it's the first time.
        False otherwise.
        """
        if self.__repo.database.last_release_s == self.__repo.hgit.current_release:
            return 're-apply'
        return 'apply'

    def __backup_file(self, release, commit=None):
        backup_dir = os.path.join(self.__repo.base_dir, 'Backups')
        if not os.path.isdir(backup_dir):
            os.mkdir(backup_dir)
        file_name = f'{self.__repo.name}-{release}'
        if commit:
            file_name = f'{file_name}-{commit}'
        return os.path.join(backup_dir, f'{file_name}.sql')

    def __save_db(self, release):
        """Save the database
        """
        commit = None
        if self.__repo.production:
            commit = self.__repo.hgit.last_commit()
        svg_file = self.__backup_file(release, commit)
        print(f'Saving the database into {svg_file}')
        if os.path.isfile(svg_file):
            utils.error(
                f"Oops! there is already a dump for the {release} release.\n")
            utils.error("Please remove it if you really want to proceed.\n", exit_code=1)
        self.__repo.database.execute_pg_command(
            'pg_dump', '-f', svg_file, stderr=subprocess.PIPE)

    def __restore_db(self, release):
        """Restore the database to the release_s version.
        """
        print(f'Restoring the database to {utils.Color.bold(release)}')
        self.__repo.model.disconnect()
        self.__repo.database.execute_pg_command('dropdb')
        self.__repo.database.execute_pg_command('createdb')
        self.__repo.database.execute_pg_command(
            'psql', '-f', self.__backup_file(release), stdout=subprocess.DEVNULL)
        self.__repo.model.ping()

    def __execute_sql(self, file_):
        "Execute sql query contained in sql file_"
        query = utils.read(file_.path).replace('%', '%%')
        if len(query) == 0:
            return
        try:
            self.__repo.model.execute_query(query)
        except (psycopg2.Error, psycopg2.OperationalError, psycopg2.InterfaceError) as err:
            utils.error(f'Problem with query in {file_.name}\n{err}\n')
            db_release = self.__repo.database.last_release_s
            previous_release = self.previous(db_release)
            self.__restore_db(previous_release)
            os.remove(self.__backup_file(previous_release))
            sys.exit(1)

    def __execute_script(self, file_):
        try:
            subprocess.run(
                ['python', file_.path],
                env=os.environ.update({'PYTHONPATH': self.__repo.base_dir}),
                shell=False, check=True)
        except subprocess.CalledProcessError as err:
            utils.error(f'Problem with script {file_}\n{err}\n')
            db_release = self.__repo.database.last_release_s
            previous_release = self.previous(db_release)
            self.__restore_db(previous_release)
            os.remove(self.__backup_file(previous_release))
            sys.exit(1)

    def apply(self, release, force=False, save_db=True):
        "Apply the release in 'path'"
        if self.__repo.hgit.repos_is_clean():
            self.__repo.hgit.rebase('hop_main')
        db_release = self.__repo.database.last_release_s
        changelog_msg = ''
        if self.__check_apply_or_re_apply() == 'apply' and save_db:
            self.__save_db(db_release)
        elif not self.__repo.production:
            if not force:
                okay = input(f'Do you want to re-apply the release {release} [y/N]?') or 'y'
                if okay.upper() != 'Y':
                    sys.exit()
            self.__restore_db(self.previous(db_release))
        print(f'Applying release {utils.Color.bold(release)}')
        files = []
        major, minor, patch = release.split('.')
        path = os.path.join(self.__patches_base_dir, major, minor, patch)
        for file_ in os.scandir(path):
            files.append({'name': file_.name, 'file': file_})
        for elt in pydash.order_by(files, ['name']):
            file_ = elt['file']
            extension = file_.name.split('.').pop()
            if file_.name == 'MANIFEST.py':
                changelog_msg = json.loads(utils.read(file_))['changelog_msg']
            if (not file_.is_file() or not (extension in ['sql', 'py'])):
                continue
            print(f'+ {file_.name}')

            if extension == 'sql':
                self.__execute_sql(file_)
            elif extension == 'py':
                self.__execute_script(file_)
        if not self.__repo.production:
            modules.generate(self.__repo)
        self.__repo.database.register_release(major, minor, patch, changelog_msg)

    @property
    def state(self):
        "The state of a patch"
        if not self.__repo.production:
            resp = ['[Releases in development]']
            if len(self.__changelog.releases_in_dev) == 0:
                resp.append("No release in development.\nUse `hop prepare-release`.")
            for release in self.__changelog.releases_in_dev:
                resp.append(f'- {release} (branch hop_{release})')
        else:
            resp = ['[Releases to apply]']
            if len(self.__changelog.releases_to_apply_in_prod) == 0:
                resp.append("No new release to apply.")
            for release in self.__changelog.releases_to_apply_in_prod:
                resp.append(f'- {release}')
        return '\n'.join(resp)


    def undo(self, database_only=False):
        "Undo a patch."
        db_release = self.__repo.database.last_release_s
        previous_release = self.previous(db_release)
        self.__restore_db(previous_release)
        if not database_only:
            modules.generate(self.__repo)
        os.remove(self.__backup_file(previous_release))

    def release(self, push):
        "Release a patch"
        # We must be on the first branch in devel (see CHANGELOG)
        next_release = self.__repo.changelog.releases_in_dev[0]
        next_branch = f'hop_{next_release}'
        if next_branch != self.__repo.hgit.branch:
            utils.error(f'Next release is {next_release} Please switch to the branch {next_branch}!\n', 1)
        # Git repo must be clean
        if not self.__repo.hgit.repos_is_clean():
            utils.error(
                f'Please `git commit` your changes before releasing {next_release}.\n', exit_code=1)
        # The patch must be applied and the last to apply
        if not self.__repo.database.last_release_s == next_release:
            utils.error(f'Please `hop test-release` before releasing {next_release}.\n', exit_code=1)
        # If we undo the patch (db only) and re-apply it the repo must still be clear.
        self.undo(database_only=True)
        self.apply(next_release, force=True)
        if not self.__repo.hgit.repos_is_clean():
            utils.error(
                'Something has changed when re-applying the release. This should not happen.\n',
                exit_code=1)
        # the tests must pass
        try:
            subprocess.run(['pytest', self.__repo.name], check=True)
        except subprocess.CalledProcessError:
            utils.error('Tests must pass in order to release.\n', exit_code=1)
        # So far, so good
        self.__repo.hgit.rebase_to_hop_main(push)

    def upgrade_prod(self):
        "Upgrade the production"
        self.__save_db(self.__repo.database.last_release_s)
        for release in self.__repo.changelog.releases_to_apply_in_prod:
            self.apply(release, save_db=False)

    def restore(self, release):
        "Restore the database and package to a release (in production)"
        self.__restore_db(release)
        # Do we have the backup
