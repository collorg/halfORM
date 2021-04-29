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

import pydash
import argparse
from datetime import date
import subprocess
import os
import psycopg2
import sys
import yaml
from half_orm.model_errors import UnknownRelation
from half_orm.model import Model, CONF_DIR

CONFIG_FILE = 'patch.yml'
PATCH_YML_TMPL = """db_connection_file_name: {}
production: {}
"""
CURRENT = ''
ARGS = ''
CONF = ''
MODEL = None
DBNAME = ''
ORIGDIR = ''
MODULE_DIR = ''

def update_release(release, changelog, commit, issue):
    "Mise à jour de la table meta.release"
    new_release = MODEL.get_relation_class('meta.release')(
        major=release['major'], minor=release['minor'], patch=int(release['patch']),
        commit=commit
    )
    if len(new_release) == 0:
        new_release.changelog = changelog
        new_release.insert()
    new_release = new_release.get()
    if issue:
        num, issue_release = str(issue).split('.')
        MODEL.get_relation_class('meta.release_issue')(
            num=num, issue_release=issue_release,
            release_major=new_release['major'],
            release_minor=new_release['minor'],
            release_patch=new_release['patch'],
            release_pre_release=new_release['pre_release'],
            release_pre_release_num=new_release['pre_release_num'],
            changelog=changelog
        ).insert()

def get_sha1_commit(patch_script):
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
            exit_(1)
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

def save_database():
    """Dumps the database"""
    if not os.path.isdir('./svg'):
        os.mkdir('./svg')
    svg_file = f'./svg/{MODEL._dbname}-{CURRENT}.sql'
    if os.path.isfile(svg_file):
        sys.stderr.write(f"Oops! there is already a dump for the {CURRENT} release.\n")
        sys.stderr.write(f"Please remove {svg_file} if you realy want to proceed.\n")
        sys.exit(1)
    subprocess.run(['pg_dump', MODEL._dbname, '-f', svg_file])

def apply_patch(path, release, commit=None, issue=None):
    "Applique le patch et met à jour la base"
    save_database()
    patch_path = f'Patches/{path}/'
    if not os.path.exists(patch_path):
        raise Exception('The directory {patch_path} does not exists')

    changelog_file = os.path.join(patch_path, 'CHANGELOG.md')
    bundle_file = os.path.join(patch_path, 'BUNDLE')

    if not os.path.exists(changelog_file):
        sys.stderr.write("ERROR! {} is missing!\n".format(changelog_file))
        exit_(1)

    if commit is None:
        commit = get_sha1_commit(changelog_file)

    changelog = open(changelog_file).read()

    print(changelog)
    try:
        with open(bundle_file) as bundle_file_:
            bundle_issues = [ issue.strip() for issue in bundle_file_.readlines() ]
            update_release(release, changelog, commit, None)
            _ = [
                apply_issue(issue, release, commit, issue)
                for issue in bundle_issues
            ]
    except FileNotFoundError:
        pass

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
                ret_val = MODEL.execute_query(query)
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

    update_release(release, changelog, commit, issue)

def apply_issue(issue, release, commit=None, bundled_issue=None):
    "Applique un issue"
    apply_patch('devel/issues/{}'.format(issue), release, commit, bundled_issue)

def get_next_release():
    global CURRENT
    "Renvoie en fonction de part le numéro de la prochaine release"
    last_release = MODEL.get_relation_class('meta.view.last_release')().get().to_dict()
    CURRENT = '{major}.{minor}.{patch}'.format(**last_release)
    print("LAST RELEASE: {major}.{minor}.{patch} at {time}".format(**last_release))
    to_zero = []
    for part in ['patch', 'minor', 'major']:
        next_release = dict(last_release)
        next_release[part] = last_release[part] + 1
        for sub_part in to_zero:
            next_release[sub_part] = 0
        next_release_path = '{major}/{minor}/{patch}'.format(**next_release)
        print("Trying {}".format(next_release_path.replace("/", ".")))
        if os.path.exists('Patches/{}'.format(next_release_path)):
            print("FOUND PATCH: {major}.{minor}.{patch}".format(**next_release))
            return {'release':next_release, 'path': next_release_path}
        to_zero.append(part)

def exit_(retval=0):
    print("exit")
    "Exit after restoring ORIGDIR"
    sys.exit(retval)

def initialisation():
    "Initialise le système de patch en créant les tables meta.release et meta.last_release"
    #TODO: voir si les tables sont déjà présentes
    print(f"Initialising the patch system for the '{DBNAME}' database.")
    sql_dir = f"{MODULE_DIR}/halfORM_db_patch_system"
    MODEL.execute_query(open(f"{sql_dir}/meta.release.sql").read())
    MODEL.execute_query(open(f"{sql_dir}/meta.last_release.sql").read())
    MODEL.execute_query(open(f"{sql_dir}/meta.release_issue.sql").read())
    MODEL.execute_query(
        "insert into meta.release values (0,0,0, '', 0, now(),'First release', '{}')".format(
            date.today()))

def patch(dbname, create=False):
    "Main"
    global ARGS, CONF, MODEL, DBNAME, ORIGDIR, MODULE_DIR, CURRENT

    ORIGDIR = os.path.abspath('.')
    MODULE_DIR = os.path.dirname(__file__)

    DBNAME = dbname
    try:
        MODEL = Model(DBNAME)
    except psycopg2.OperationalError:
        print(f'\nERROR! The "{DBNAME}" database does not exist!\n')
        sys.exit(1)

    if create:
        CURRENT = 'pre-patch'
        save_database()
        initialisation()
    else:
        next_ = get_next_release()
        if next_:
            apply_patch(next_['path'], next_['release'])
        else:
            print("No patch to apply!")
            sys.exit(1)
