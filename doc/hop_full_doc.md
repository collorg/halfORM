# The `hop` command - The complete documentation

This is a complete rewrite of the `hop` command.

`hop` uses a semantic versioning scheme. It allows you to maintain multiple versions
of your application.
On a fresh install, with `hop new --devel`, the release version of your application is `0.0`. The `0` majors versions should be considered unstable until the release 1.0.0.

It should conform to [semver](http://semver.org/).

The releases state:
* active: still maintained. receives `bugfix`, `security` patches.
* deprecated: can only receive `security` patches;
* inactive: EOL. no more patches. This release must be upgraded to the next
  active release.

The releases status:
* alpha: `breaking-change` patches can still be applied. New `features` can still
  be added;
* beta: no more `breaking-change` or `features` patches;
* stable: only `bugfix` patches;

## `hop` sub-commands

* `prepare-release <major|minor>`: prepares the next `major` (X) or `minor` (Y) 
  release. Creates the corresponding <X.Y>.x branch. In case of a `major` release,
  `Y` is equal to 0. The `hop new --devel` command creates the `0.0.x` branch.
* `apply-release <X.Y>`: This sub-command switches to the `X.Y.x` branch and...
* `commit-release`: Tags the release branch.
* `publish-release`: Tags the release branch.
* `prepare-pacth`: This sub-command creates a patch branch for your application.
* `apply-patch <release>`: This sub-command switches to the patch branch and...


### `prepare-patch <name>`

This command will create a patch branch for your application. it has the following options:

* `--type`: the type of patch to be created. It can be `security`, `bugfix`, `feature`, or `chore`.
  * a `security` patch must be applied to all the maintained releases;
  * a `bugfix` patch is applied to the releases concerned;
  * a `feature` patch is applied to the next `minor` or `major` release;
* `--message`: the message that will be used in the patch
* `--breaking-change`: can only be applied to the next `major` release except if
  the current `major` release is `0`.

### `apply-patch <[release, ...]>`

A patch can be applied to any of the maintained releases or releases in preparation. 