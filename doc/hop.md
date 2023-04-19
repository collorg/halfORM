# The half_orm packager [alpha][WIP]

**This work is in progress and subject to major changes.**

`half_orm` comes with a command line interface tool. The `hop` script allows you to initialise, develop and maintain a half_orm package in sync with a PostgreSQL model. The `half_orm packager` takes a GitOps approach by providing a Git-based workflow for development and deployment.

`hop` distinguishes between two environment modes: development and production. To get some help on a particular command, type: `hop <command> --help`.

### Create a `hop` repository

| Command | Description |
| -- | -- |
| new | creates a Python package from a PostgreSQL database |

**IMPORTANT WARNING!** The `--devel` option of the `new` command adds the following tables and views to the database model:

* half_orm_meta.hop_release,
* half_orm_meta.hop_release_issue,
* "half_orm_meta.view".hop_last_release,
* "half_orm_meta.view".hop_penultimate_release.

## Development mode

### Inside a hop repository created **with** the option `--devel`

| Command | Description |
| -- | -- |
| prepare | prepares a new release |
| apply | applies the patches of the release being prepared |
| undo | reverts the model back to the previous release |
| release | commits the release in preparation |

#### Workflow

The green arrows represent the typical workflow for patching a model:

<img title="hop workflow" alt="Alt text" style="background-color: white" src="https://github.com/collorg/halfORM/blob/main/doc/hop_workflow.svg" style="width: 70%">

### Inside a hop repository created **without** the option `--devel`

| Command | Description |
| -- | -- |
| sync-package | synchronizes the package with the model |


## Production mode

Inside a `hop` repository, and in production mode, two commands are available:

| Command | Description |
| -- | -- |
| upgrade | upgrades the database to the latest release |
| restore | restores the database to a previous release |


## Documentation

Check the `hop` in action with the [dummy test script](https://github.com/collorg/halfORM/blob/main/half_orm/packager/test/dummy_test.sh).
