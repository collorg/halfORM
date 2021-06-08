#!/usr/bin/env python3
#-*- coding: utf-8 -*-

"""Patche la base de donnée

Détermine le patch suivant et l'applique. Les patchs sont appliqués un
par un.

Si l'option -i <no de patch> est utilisée, le patch sera pris dans
Patches/devel/issues/<no de patch>.
Le numéro de patch dans la table meta.release sera 9999.9999.<no de patch>
L'option -i n'est pas utilisable si patch.yml positionne PRODUCTION à True.
"""

from datetime import date
import os
import sys
import subprocess
import psycopg2
import pydash
from half_orm.model_errors import UnknownRelation


class Patch:
    def __init__(self, model, create_mode=False, init_mode=False):
        self.model = model
        self.__dbname = self.model._dbname
        self.__create_mode = create_mode
        self.__init_mode = init_mode
        self.__orig_dir = os.path.abspath('.')
        self.__module_dir = os.path.dirname(__file__)
        self.__last_release_s = None
        self.__release = None
        self.__release_s = ''
        self.__release_path = None

    def patch(self):
        """
        """
        if self.__create_mode or self.__init_mode:
            self.__last_release_s = 'pre-patch'
            self.save_database()
            return self._init()
        self._patch()
        os.chdir(self.__orig_dir)
        return self.__release_s

    def update_release(self, changelog, commit, issue):
        "Mise à jour de la table meta.release"
        new_release = self.model.get_relation_class('meta.release')(
            major=self.__release['major'],
            minor=self.__release['minor'],
            patch=int(self.__release['patch']),
            commit=commit
        )
        if len(new_release) == 0:
            new_release.changelog = changelog
            new_release.insert()
        new_release = new_release.get()
        if issue:
            num, issue_release = str(issue).split('.')
            self.model.get_relation_class('meta.release_issue')(
                num=num, issue_release=issue_release,
                release_major=new_release['major'],
                release_minor=new_release['minor'],
                release_patch=new_release['patch'],
                release_pre_release=new_release['pre_release'],
                release_pre_release_num=new_release['pre_release_num'],
                changelog=changelog
            ).insert()

    def get_sha1_commit(self, patch_script):
        "Renvoie le sha1 du dernier commmit"
        repo_is_clean = subprocess.Popen(
            "git status --porcelain", shell=True, stdout=subprocess.PIPE)
        repo_is_clean = repo_is_clean.stdout.read().decode().strip().split('\n')
        repo_is_clean = [line for line in repo_is_clean if line != '']
        if repo_is_clean:
            print("WARNING! Repo is not clean:\n\n{}".format('\n'.join(repo_is_clean)))
            cont = input("\nApply [y/N]?")
            if cont.upper() != 'Y':
                print("Aborting")
                self.exit_(1)
        commit = subprocess.Popen(
            "git log --oneline --abbrev=-1 --max-count=1 {}".format(
            os.path.dirname(patch_script)
        ), shell=True, stdout=subprocess.PIPE)
        commit = commit.stdout.read().decode()
        if commit.strip():
            commit = commit.split()[0] # commit is the commit sha1
        else:
            sys.stderr.write("WARNING! Running in test mode (logging the date as commit).\n")
            commit = "{}".format(date.today())
        return commit

    def save_database(self):
        """Dumps the database"""
        if not os.path.isdir('./Backups'):
            os.mkdir('./Backups')
        svg_file = f'./Backups/{self.__dbname}-{self.__last_release_s}.sql'
        if os.path.isfile(svg_file):
            sys.stderr.write(f"Oops! there is already a dump for the {self.__last_release_s} release.\n")
            sys.stderr.write(f"Please remove {svg_file} if you realy want to proceed.\n")
            sys.exit(1)
        subprocess.run(['pg_dump', self.__dbname, '-f', svg_file])

    def _patch(self, commit=None, issue=None):
        "Applique le patch et met à jour la base"
        self.__get_next_release()
        if self.__release_s == '':
            return
        self.save_database()
        patch_path = f'Patches/{self.__release_path}/'
        if not os.path.exists(patch_path):
            raise Exception('The directory {patch_path} does not exists')

        changelog_file = os.path.join(patch_path, 'CHANGELOG.md')
        # bundle_file = os.path.join(patch_path, 'BUNDLE')

        if not os.path.exists(changelog_file):
            sys.stderr.write("ERROR! {} is missing!\n".format(changelog_file))
            self.exit_(1)

        if commit is None:
            commit = self.get_sha1_commit(changelog_file)

        changelog = open(changelog_file).read()

        print(changelog)
        # try:
        #     with open(bundle_file) as bundle_file_:
        #         bundle_issues = [ issue.strip() for issue in bundle_file_.readlines() ]
        #         self.update_release(changelog, commit, None)
        #         _ = [
        #             self.apply_issue(issue, commit, issue)
        #             for issue in bundle_issues
        #         ]
        # except FileNotFoundError:
        #     pass

        ret_val = 0

        files = []
        for f in os.scandir(patch_path):
            files.append({'name': f.name, 'file': f})
        for elt in pydash.order_by(files, ['name']):
            f = elt['file']
            extension = f.name.split('.').pop()
            if (not f.is_file() or not (extension in ['sql', 'py'])):
                continue
            print(f'+ {f.name}')

            if extension == 'sql':
                query = open(f.path, 'r').read().replace('%', '%%')
                if len(query) <= 0:
                    continue

                try:
                    ret_val = self.model.execute_query(query)
                except psycopg2.Error as err:
                    sys.stderr.write(
                        f"""WARNING! SQL error in :{f.path}\n
                            QUERY : {query}\n
                            {err}\n""")
                    continue
                except (psycopg2.OperationalError, psycopg2.InterfaceError):
                    raise Exception(f'Problem with query in {f.name}')
            if extension == 'py':
                # exécuter le script
                subprocess.Popen(f.path, shell=True).wait()

        self.update_release(changelog, commit, issue)

    # def apply_issue(self, issue, commit=None, bundled_issue=None):
    #     "Applique un issue"
    #     self._patch('devel/issues/{}'.format(issue), commit, bundled_issue)

    def __get_next_release(self):
        "Renvoie en fonction de part le numéro de la prochaine release"
        last_release = next(self.model.get_relation_class('meta.view.last_release')().select())
        self.__last_release_s = '{major}.{minor}.{patch}'.format(**last_release)
        msg = "LAST RELEASE: {major}.{minor}.{patch} at {time}"
        if 'date' in last_release:
            msg = "LAST RELEASE: {major}.{minor}.{patch}: {date} at {time}"
        print(msg.format(**last_release))
        to_zero = []
        for part in ['patch', 'minor', 'major']:
            next_release = dict(last_release)
            next_release[part] = last_release[part] + 1
            for sub_part in to_zero:
                next_release[sub_part] = 0
            next_release_path = '{major}/{minor}/{patch}'.format(**next_release)
            next_release_s = '{major}.{minor}.{patch}'.format(**next_release)
            print(f"Trying {next_release_s}")
            if os.path.exists('Patches/{}'.format(next_release_path)):
                print("FOUND PATCH: {major}.{minor}.{patch}".format(**next_release))
                self.__release = next_release
                self.__release_s = next_release_s
                self.__release_path = next_release_path
                return

    def exit_(self, retval=0):
        "Exit after restoring orig dir"
        os.chdir(self.__orig_dir)
        sys.exit(retval)

    def _init(self):
        "Initialise le système de patch en créant les tables meta.release et meta.last_release"

        print(f"Initialising the patch system for the '{self.__dbname}' database.")
        sql_dir = f"{self.__module_dir}/db_patch_system"
        release = True
        last_release = True
        penultimate_release = True
        release_issue = True
        try:
            self.model.get_relation_class('meta.release')
        except UnknownRelation:
            release = False
        try:
            self.model.get_relation_class('meta.last_release')
        except UnknownRelation:
            last_release = False
        try:
            self.model.get_relation_class('meta.penultimate_release')
        except UnknownRelation:
            penultimate_release = False
        try:
            self.model.get_relation_class('meta.release_issue')
        except UnknownRelation:
            release_issue = False
        patch_confict = release or last_release or release_issue or penultimate_release
        if patch_confict:
            sys.stderr.write('Does the database have a patch system?\n')
            sys.stderr.write('Not installing the patch system!\n')
            return
        if not os.path.exists('./Patches'):
            os.mkdir('./Patches')
            open('./Patches/README', 'w').write(open(f"{sql_dir}/README").read())
        self.model.execute_query(open(f"{sql_dir}/meta.release.sql").read())
        self.model.execute_query(open(f"{sql_dir}/meta.last_release.sql").read())
        self.model.execute_query(open(f"{sql_dir}/meta.view.penultimate_release.sql").read())
        self.model.execute_query(open(f"{sql_dir}/meta.release_issue.sql").read())
        self.model.execute_query(
            "insert into meta.release values (0,0,0, '', 0, now(), now(),'[0.0.0] First release', '{}')".format(
                date.today()))

        print("Patch system initialized at release '0.0.0'.")
        return "0.0.0"
