# The `hop` command - The GitOps package manager for half_orm

## [WIP][alpha] This work is in progress and subject to major changes.

`hop` is a command-line tool provided with the `half_orm` library. It allows you to manage the full lifecycle of your PostgreSQL/Python projects, following a GitOps approach.

## Overview

The `hop` tool distinguishes between two environment modes: development and production. It offers a Git-based workflow for the development and deployment of your `half_orm` projects.

<img title="hop workflow" alt="hop workflow" src="https://github.com/collorg/halfORM/blob/main/doc/hop_workflow.png" style="width: 70%">

## Initializing a `hop` project

To create a new `hop` project from an existing PostgreSQL database, use the `new` command:

```bash
hop new <database_name> [--devel]
```

The `--devel` option is important. It allows adding specific tables and views to the database model, which are necessary for version tracking with `hop`.

## Development

Once the project is initialized, you can start working on your data model and Python code in a `hop` directory.

### Version management

Version management with `hop` is done incrementally by preparing successive "releases":

- `hop prepare [-l <level>] [-m <message>]`: Prepares a new release (level: `patch`, `minor`, or `major`)
- `hop apply`: Applies the changes for the release in preparation
- `hop release [--push]`: Validates and pushes the release in preparation

You can also:

- `hop undo`: Cancel the changes for the release being prepared

### Workflow example

1. `hop prepare -l patch -m "Bug fixes"`
2. Modify the SQL files in `Patches/<version>/...`
3. Modify your Python code
4. `hop apply` to apply the changes
5. `git add/commit ...`
6. `hop release --push` to validate and push the release

## Production

In a production environment, `hop` allows you to deploy and manage different versions of your project.

- `hop upgrade`: Updates the database to the latest published release
- `hop restore <version>`: Restores the database to a specific release version

## Automated testing

Before validating a new release with `hop release`, the tool automatically runs the tests defined in your project (using pytest by default). This ensures the integrity of your code and data model at each step.

## Additional resources

- [Test examples](https://github.com/collorg/halfORM/blob/main/half_orm/packager/test/dummy_test.sh) for the `hop` command
- [TODO] [Complete documentation](https://github.com/collorg/halfORM/blob/main/doc/hop_full_doc.md) for the `hop` tool

With `hop`, you benefit from a powerful tool to manage the full lifecycle of your `half_orm` projects, following modern development best practices such as continuous integration, automated testing, and continuous deployment.