"Provides the HGit class"

import os
import subprocess
from git import Repo
from git.exc import GitCommandError

from half_orm.packager import utils
from half_orm.packager.manifest import Manifest

class HGit:
    "Manages the git operations on the repo."
    def __init__(self, repo=None):
        self.__repo = repo
        self.__base_dir = None
        self.__git_repo: Repo = None
        if repo:
            self.__base_dir = repo.base_dir
            self.__post_init()

    def __post_init(self):
        self.__git_repo = Repo(self.__base_dir)
        self.__current_branch = self.branch

    def __str__(self):
        res = ['[Git]']
        res.append(f'- current branch: {self.__current_branch}')
        clean = self.repos_is_clean()
        clean = utils.Color.green(clean) \
            if clean else utils.Color.red(clean)
        res.append(f'- repo is clean: {clean}')
        res.append(f'- last commit: {self.last_commit()}')
        return '\n'.join(res)

    def init(self, base_dir, release='0.0.0'):
        "Initiazes the git repo."
        cur_dir = os.path.abspath(os.path.curdir)
        self.__base_dir = base_dir
        try:
            subprocess.run(['git', 'init', base_dir], check=True)
            self.__git_repo = Repo(base_dir)
            os.chdir(base_dir)
            self.__git_repo.git.add('.')
            self.__git_repo.git.commit(m=f'[{release}] hop new {os.path.basename(base_dir)}')
            self.__git_repo.git.checkout('-b', 'hop_main')
            os.chdir(cur_dir)
            self.__post_init()
        except GitCommandError as err:
            utils.error(
                f'Something went wrong initializing git repo in {base_dir}\n{err}\n', exit_code=1)
        return self

    @property
    def branch(self):
        "Returns the active branch"
        return str(self.__git_repo.active_branch)

    @property
    def current_release(self):
        "Returns the current branch name without 'hop_'"
        return self.branch.replace('hop_', '')

    @property
    def is_hop_patch_branch(self):
        "Returns True if we are on a hop patch branch hop_X.Y.Z."
        try:
            major, minor, patch = self.current_release.split('.')
            return bool(1 + int(major) + int(minor) + int(patch))
        except ValueError:
            return False

    def repos_is_clean(self):
        "Returns True if the git repository is clean, False otherwise."
        return not self.__git_repo.is_dirty(untracked_files=True)

    def last_commit(self):
        """Returns the last commit
        """
        commit = str(list(self.__git_repo.iter_commits(self.branch, max_count=1))[0])[0:8]
        assert self.__git_repo.head.commit.hexsha[0:8] == commit
        return commit

    def branch_exists(self, branch):
        "Returns True if branch is in branches"
        return branch in self.__git_repo.heads

    def set_branch(self, release_s):
        """Checks the branch

        Either hop_main or hop_<release>.
        """
        rel_branch = f'hop_{release_s}'
        self.add(self.__repo.changelog.file)
        if str(self.branch) == 'hop_main' and rel_branch != 'hop_main':
            # creates the new branch
            self.__git_repo.git.commit('-m', f'[hop][main] Add {release_s} to Changelog')
            self.__git_repo.create_head(rel_branch)
            self.__git_repo.git.checkout(rel_branch)
            self.__git_repo.git.add('Patches')
            self.__git_repo.git.commit('-m', f'[hop][{release_s}] Patch skeleton')
            self.cherry_pick_changelog(release_s)
            print(f'NEW branch {rel_branch}')
        elif str(self.branch) == rel_branch:
            print(f'On branch {rel_branch}')

    def cherry_pick_changelog(self, release_s):
        "Sync CHANGELOG on all hop_x.y.z branches in devel different from release_s"
        branch = self.__git_repo.active_branch
        self.__git_repo.git.checkout('hop_main')
        commit_sha = self.__git_repo.head.commit.hexsha[0:8]
        for release in self.__repo.changelog.releases_in_dev:
            if release != release_s:
                self.__git_repo.git.checkout(f'hop_{release}')
                self.__git_repo.git.cherry_pick(commit_sha)
                # self.__git_repo.git.commit('--amend', '-m', f'[hop][{release_s}] CHANGELOG')
        self.__git_repo.git.checkout(branch)

    def rebase_devel_branches(self, release_s):
        "Rebase all hop_x.y.z branches in devel different from release_s on hop_main:HEAD"
        for release in self.__repo.changelog.releases_in_dev:
            if release != release_s:
                self.__git_repo.git.checkout(f'hop_{release}')
                self.__git_repo.git.rebase('hop_main')

    def rebase_to_hop_main(self, push=False):
        "Rebase a hop_X.Y.Z branch to hop_main"
        release = self.current_release
        try:
            self.__git_repo.git.pull('origin', 'hop_main')
            hop_main_last_commit = self.__git_repo.commit('hop_main').hexsha[0:8]
            self.__git_repo.git.rebase('hop_main')
            self.__git_repo.git.checkout('hop_main')
            self.__git_repo.git.rebase(f'hop_{release}')
            self.__repo.changelog.update_release(
                self.__repo.database.last_release_s,
                self.__repo.hgit.last_commit(),
                hop_main_last_commit)
            # version_file = os.path.join(self.__base_dir, self.__repo.name, 'version.txt')
            # utils.write(version_file, release)
            # self.__git_repo.git.add(version_file)
            patch_dir = os.path.join(self.__base_dir, 'Patches', *release.split('.'))
            manifest = Manifest(patch_dir)
            message = f'[{release}] {manifest.changelog_msg}'
            self.__git_repo.git.commit('-m', message)
            self.__git_repo.git.tag(release, '-m', release)
            self.cherry_pick_changelog(release)
            if push:
                self.__git_repo.git.push()
                self.__git_repo.git.push('-uf', 'origin', release)
        except GitCommandError as err:
            utils.error(f'Something went wrong rebasing hop_main\n{err}\n', exit_code=1)

    def add(self, *args, **kwargs):
        "Proxy to git.add method"
        return self.__git_repo.git.add(*args, **kwargs)

    def commit(self, *args, **kwargs):
        "Proxy to git.commit method"
        return self.__git_repo.git.commit(*args, **kwargs)

    def rebase(self, *args, **kwargs):
        "Proxy to git.commit method"
        return self.__git_repo.git.rebase(*args, **kwargs)

