# 0.13.3 -- hop 0.1.0 alpha 18 (2024-11-11)

* [relation] New relation.transaction decorator (replaces Relation.ho_transaction). (07f3a07)
* [relation] Replace attribute _model by _ho_model. (8d55b6a)
* [test] ho_distinct argument values. (d45242c)
* [test][relation] test dict behavior (keys, items and __getitem__). (076139f)
* [test] utils. Fix CI (9e5223f)
* [test] utils. (8f0352d)
* [test] ho_count with fkeys. (8928400)
* [hop] Pylint score improvement (8d218c9)
* [hop] Add repo base dir to PYTHONPATH. (064576f)
* [field] Add missing import. (63c24dd)
* [test][relation] ho_freeze and ho_unfreeze (4bcb2f5)
* [relation] Reintroduction of deprecated methods to be remove with release 1.0.0 (680cd5f)
* [relation] refactor ho_count. (89d2f5d)
* [sonarcloud] More fixes. (a99e57d)
* [refactor] Fix some issues pointed out by Sonarcloud. (b106f74)
* [relation] Use context manager for cursors. (2260f32)
* [hop] Replace kwargs with the explicit list of fields. (b947737)
* [field] Adds the Field.py_type property returning the Python type corresponding to the SQL type. (ee0202e)

# 0.13.2 -- hop 0.1.0 alpha 17 (2024-10-31)

## BREAKING CHANGE

Relation methods select, insert, upgrade, delete deprecated in 0.8.0 have now been removed. Use ho_select, ho_insert, ho_upgrade and ho_delete instead.

* [hop] sort imports in ho_dataclasses.py (HEAD -> main) (801385b)
* [hop] Add Fkeys to dataclasses. (10ba318)
* [hop][relation] Refactor. Add DC_Relation to improve developper experience. (a9e2dda)
* [CI] Keep psycopg2 2.9.9 to preserve Python 3.7 compatibility. (f9c0380)
* [CI] Bump to psycopg 2.9.10 for Python 3.13 compatibility. (e092e3b)
* [CI/Github] Fails with Python 3.13. (2a2d897)
* [CI/Github] Add PostgreSQL 17 (1699e1a)
* [CI] Add Python 3.13 (7687c5e)
* [BREAKING CHANGE] Python 3.6 is no longer supported (89f49c1)
* [hop] Use of dataclasses to improve developer experience. (a61beb0)
* [test] coverage utils. (66b64bb)

# 0.13.1 -- hop 0.1.0 alpha 16 (2024-09-11)

* [test] Test utils.check_attribute_name. (521c922)
* [hop] Fix: empty keys in Fkeys were taken into account when generating relation class attributes. (dba5b22)

# 0.13.0 (2024-09-10)

## BREAKING CHANGE

As of version 0.13, the `Relation.ho_transaction` decorator is deprecated and replaced by
the `Transaction(<model>)` context manager (see the [readme](https://github.com/collorg/halfORM?tab=readme-ov-file#dml-the-ho_insert-ho_select-ho_update-ho_delete-methods)).

* [readme] remove deprecated ho_transaction example. (ac423af)
* [field] Marks the deprecated _unset method as not to be tested. (1f5a278)
* [transaction][BREAKING CHANGE] Transactions are now managed by a context manager. (628ceb2)
* [relation] The Relation._model object must be the one used to generate the relation class. (2bdcdb7)
* [test] Add -s option to pytest. (a7c3be0)
* [field] Do not use deprecated _unset method to clear field. (6cc2dce)

# 0.12.1 -- hop 0.1.0 alpha 15 (2024-09-06)

* [field][BREAKING CHANGE] list and set values are cast to tuples. (e215d1a)
* [relation] Remove __cursor attribute. (1d205bb)
* Bump cryptography from 42.0.5 to 43.0.1 (fee3fb6)
* [hop][relation] Emmit a warning if a column is a Python keyword or not a valid attribute name. (cfff9ef)
* [relation] __len__ will be removed in the release 0.13. Warning message with location issued when used. (00e093c)

# 0.12.0 (2024-08-28)

## BREAKING CHANGE

 From version 0.12 onward, the *`Relation.__len__`* method has been deprecated.
 It is replaced by the `Relation.ho_count` method.

*The code `len(Person())` must be replaced by `Person().ho_count()`*.

> The problem was that the Python builtin function `list` triggers the `__len__` method if it exists. So the
> code `list(Person())` was triggering two requests on the database : frist a SQL `select count`
> and then the SQL `select`.


* [hop] Remove git diff from dummy_test.sh (c8e3bd8)
* Add requirements-dev.txt (1047292)
* Code cleanup. (89fc6da)
* [relation_factory] deprecated decorator has been moved to utils module. (37f25ef)
* [relation][BREAKING CHANGE] ho_count replaces __len__. (a7742af)
* [test] Remove duplicate test. (9440c19)
* Code clean-up (13f4be6)
* Remove examples directory. (a4bf44b)
* [relation] Fix wrong order of foreign key fields in relation representation. (c8abf92)
* [test] Coverage. (7b055b2)
* [fkeys] Detect loops in foreign key settings. (50068fa)

# 0.11.1 -- hop 0.1.0 alpha 14 (2024-08-23)

* [hop] Add field and foreign key declarations to allow autocompletion in IDEs. (cb5738c)
* Bump zipp from 3.18.1 to 3.19.1 (012d4ce)
* Bump certifi from 2024.2.2 to 2024.7.4 (5222b58)
* [readme] Add sql injection warning for the Model.execute_query method. (d729ead)

# 0.11.0 (2024-05-26)

## BREAKING CHANGE

The `ho_join` methode has been removed. Use foreign keys instead. The old code (see README):

```#python
lagaffe = Person(last_name='Lagaffe')
res = lagaffe.ho_join(
    (Comment(), 'comments', ['id', 'post_id']),
    (Post(), 'posts', 'id')
)
```

becomes:

```#python
res = []
lagaffe = Person(last_name='Lagaffe')
for idx, pers in enumerate(lagaffe):
    res.append(pers)
    res[idx] = {}
    posts = Person(**pers).post_rfk()
    res[idx]['posts'] = list(posts.ho_select('id'))
    res[idx]['comments'] = list(posts.comment_rfk().ho_select('id', 'post_id'))
```


* [README] Use of pepy.tech for download badge. (2764dc2)
* [README] ... (6188323)
* [README] Update links on badges. (e7a0ba2)
* --- updated-dependencies: - dependency-name: requests   dependency-type: indirect ... (ef93b05)
* Update README.md (219f194)
* Python 3.6 is not supported by github actions/setup-python@v5. Stop testing on github. Python 3.6 is tested on Gitlab. (3552ec3)
* [info] Python 3.6 is supported. (53a3d79)
* Update license. (c2b28e6)
* [doc] Why half_orm. (d4fb6b2)
* [relation][BREAKING CHANGE] Remove ho_join. See README.md. (76d44b1)

# 0.10.5 -- hop 0.1.0a13 (2024-05-07)

* [hop]  now generates the ho_dataclasses module containing a dataclass for each relation/view in the model. (57b0e84)

# 0.10.4 -- hop 0.1.0a12 (2024-04-30)

* [relation] Check that the value is valid for ho_limit an ho_offset methods. (cdc6e9b)

# 0.10.3 -- hop 0.1.0a12 (2024-04-30)

* [hop] Remove last reference to half-orm-packager in Pipfile template. (11b79a0)

# 0.10.2 -- hop 0.1.0a11 (2024-04-30)

* [hop] Remove references to obsolete half_orm_packager. (5b2a234)

# 0.10.1 -- hop 0.1.0a10 (2024-04-26)

* [hop] Fix. hop new was broken with devel option on an existing database. (02466c8)

# 0.10.0 -- hop 0.1.0a10 (2024-04-13)

* Remove dependency to pydash. (69e7fa2)
* [test] Adjust to one liners comments. (7f096fe)
* Cleanup. (a9365ac)
* Cleanup. (5922928)
* [relation][BREAKING CHANGE] Remove methods ho_group_by and ho_json. (a346236)
* Cleanup. (e8645e6)
* [test] Add test for relation defined by fkey. (997bca3)
* Cleanup. (044f640)
* [test] Remove duplicates in algebra test. (98c99e5)
* Cleanup. (41ea4e9)
* [hop] Do not check rebase twice. (56dfd11)
* Fix broken hop_test. (31df016)
* [WIP][model] Cleanup. (6ed901b)
* [WIP] Cleanup. (dc16ba1)
* Revert "[cleanup][hotest] Readability."" (848e7bd)
* Revert "[field] Clean-up." (60b2394)
* [cleanup][hotest] Readability." (a92bbda)
* [field] Clean-up. (7d141e2)
* [field] Mark _set method as deprecated. (ebaea77)
* [field][cleanup] Merge if statements. (a966ff9)
* [field][BREAKING CHANGE] Use of the set method is now mandatory to set the value of a field. (47c6c17)
* [Cleanup] Remove commented out code. (temp) (3f965d8)
* Bump idna from 3.6 to 3.7 (8a0f2b2)

## BREAKING CHANGES

Relation.ho_group_by and Relation.ho_json have been removed.

With version 0.10, it's no longer possible to set a field value directly.
You must use the `set` method to do so. Stay with version 0.9 until you have adapted your code.

### Before:

```py
Relation.field = value
```

### After

```py
Relation.field.set(value)
```

# 0.9.12 -- hop 0.1.0a10 (2024-03-29)

* [hop] Apply post patches after the modules generation. (41134a7)
* [fkeys] Add properties name and remote. (24ded98)

# 0.9.11 -- hop 0.1.0a9 (2024-03-11)

* [hop] Check that all hop_X.Y.Z in development can be rebased onto hop_main. (a8a2ea8)
* [hop][test] Move hop_test config directory. (1aaf9d9)
* [hop][prepare] Only restore database if database release is not the last release (AKA release in prod). (4561b5b)

# 0.9.10 -- hop 0.1.0a8 (2024-03-06)

* [pipenv] Bump cryptography to 42.0.5 (586ce19)
* [hop] prepare command (devel mode) now fails if the git repo is not clean. (39ebbaf)
* [github][CI] Remove misplaced matrix.postgresql-version (415b62e)
* [github][CI] Update actions to use Node.js 20 (github) (a4525c4)

# 0.9.9 -- hop 0.1.0a7 (2024-02-22)

* Bump cryptography from 42.0.2 to 42.0.4 (c02152e)

# 0.9.8 -- hop 0.1.0a7 (2024-02-06)

* [hop] Remove subprocess.run(['git', 'init' ... (870d5ae)

# 0.9.7 -- hop 0.1.0a6 (2024-01-10)

* Bump gitpython from 3.1.40 to 3.1.41 (746196d)
* [test] Remove unnecessary postgresql restart. (a99f336)
* [pipenv] Bump to Python 3.10. (bb31fb9)
* [make] Set LC_MESSAGES to C. (35931d4)
* [git] Ignore venv directories and files. (87b046d)
* [pipenv] Add pylance in dev mode. (4bce8e3)
* [test] Relation ho_description and ho_mogrify. Remove duplicate tests. (fd76802)
* Bump cryptography from 41.0.5 to 41.0.6 (a9fa76d)

# 0.9.6 -- hop 0.1.0a6 (2023-11-27)

* [error] Check error message on UnknownAttributeError. (43cc05a)
* [deps] Bump pydash to 7. (156d843)
* [relation] Check that args match column names before generating any sql. (b5e4028)

# 0.9.5 -- hop 0.1.0a6 (2023-11-21)

* [relation] @singleton decorator sets the attributes __is_signleton and __orig_args on the decorated function. (ff80877)
* [make] split tests. (23401ea)
* [CI][github] Add Python 3.12 and PostgreSQL 16. (fe4d43b)
* [CI][gitlab] Add Python 3.12. (9c8b863)

# 0.9.4 -- hop 0.1.0a6 (2023-11-14)

* [hop] Remove path from __init__.py. (bbdeed9)
* Bump gitpython from 3.1.34 to 3.1.37 (9c46991)
* Bump urllib3 from 2.0.5 to 2.0.6 (6f7c903)
* [make] Add target build. (0178a3c)
* Bump cryptography from 41.0.3 to 41.0.4 (d9e8d84)
* Update REAMDE (78ac59b)

# 0.9.3 -- hop 0.1.0a5 (2023-09-07)

* Bump gitpython from 3.1.32 to 3.1.34 (9735d3f)
* [hop] Remove gen-api command. (4fd4061)
* Bump gitpython from 3.1.31 to 3.1.32 (1289178)
* Bump cryptography from 41.0.2 to 41.0.3 (262d560)
* Bump certifi from 2023.5.7 to 2023.7.22 (ea2eceb)
* Bump cryptography from 41.0.0 to 41.0.2 (af58b62)
* [hop] Add base_dir to PYTHONPATH. (4a49763)
* [hop] Use subprocess.run to run the tests with pytest. Module doesn't behave as command. (cf910ad)

# 0.9.2 -- hop 0.1.0a4 (2023-06-09)

* [hop] Fix: wrong order in CHANGELOG. (HEAD -> main) (c763300)
* Change the representation of a Relation object. (c2a18cb)
* [hop][WIP] Add gen-api command. (d2b180e)
* Add Makefile for test and build. (04ba7c2)
* [test] pipenv install pytest-cov. (5f3647e)
* Move utils.py to half_orm directory. (0b63fbd)
* Update README. (ec7c62c)
* [hop] The __init__ module of the package exports only the MODEL of the database. (69b4d74)
* [hop] Remove db_connector.py (5a00896)
* [model] Add the method classes. (badda81)
* [pipenv] Add twine. (782f0b1)

# 0.9.1 -- hop 0.1.0a3 (2023-05-22)

* [release] 0.9.1 (hop 0.1.0a3) (tag: 0.9.1) (a87bb21)
* [test] Upgrade halftest schemas half_orm_meta and half_orm_meta.view. (ed1769a)
* [hop] Refactor view "half_orm_meta.view".hop_penultimate_release. (ba401a3)
* [hop] Fix. Restore the correct DB release in case of error. (9b9acde)
* [hop] Print error message and exit if the database is missing. (72ac017)
* [hop] Add half-orm version to hop state. (2a1b504)
* [ci][github] Tests with postgresql 9.6 to 15 (Python 3.11). (44c180f)

# 0.9.0 (2023-05-12)

* [breaking][relation] Prefix methods with 'ho_*' instead of the ugly '_ho_*'. (0d11bc0)
* [relation] Raises a DeprecationWarning error if FKEYS is defined in a module. (b9a8622)
* [packager] Check if the connection file exists before proceeding. (17884cc)

## BREAKING CHANGE

`_ho_*` methods in half_orm.relation.Relation are replaced by `ho_*`

# 0.8.0 (2023-04-20)

* [doc] Add margin to hop_workflow png. (903c707)
* [doc] pg_meta. (3ff7c7b)
* [test] Add tests for deprecated and function and procedure. (2824622)
* [model] Remove Model._check_deja_vu_class method. (c3a1d0f)
* Add relation_factory module. (dd83534)
* [WIP] (d314414)
* [test] Delete all entries from  halftest.actor.person before starting the tests. (284a79a)
* [relation] Change SQL query formatting. (7ddc6f8)
* [WIP][refactor] Add trace decorator on DML methods. (b11d196)
* pylint... (ce6a55a)
* [WIP][refactor] SQL query formatting. (808909c)
* [WIP][refactor] Add method Relation.__fkey_where. (a0b74a0)
* [WIP][refactor] Rename method Relation.__what_to_insert to Relation.__what (f05887b)
* Rename Fkey._prep_select to Fkey._fkey_prep_select. (c153df9)
* [doc] Add png image. (4d37313)
* [doc] background white for hop_workflow.svg. (14d576b)
* Fix hop mini-doc URL. Add a white background to the workflow image. (d970491)
* [WIP][doc] Add a mini-documenation for the hop command. (07091db)
* Revert "[relation] Rewrite _ho_is_empty." (786aec2)
* [relation] Rewrite _ho_is_empty. (8bc38f4)
* [test] Fkey. (22ea8a5)
* Remove unused and dead code. (cbf71ce)
* [test] Test class HoTestCase. (90b3831)
* [test] relation ioperators. (ea7bfa9)
* [test] Relation._ho_cast. (92a575c)
* [test] relation._ho_join. (30f8121)
* [relation] Add context manager for Relation objects. (4bd5c6e)
* [test] _ho_limit, _ho_offset, _ho_dict & _ho_only. (9b28577)
* [test] Set operators on foreign keys. (95b21ab)
* [test] _ho_join errors. (c5d11b2)
* [relation] _ho_dict does not return not set values. Remove __join private method. (89aea1f)
* [test] Relation repr. (6570e32)
* [relation] Mark _ho_group_by and _ho_json as not tested. (09aded8)
* [test] Check automatic reconnection after postgresql is restarted (uses sudo). (28cf326)

# 0.8.0rc11 (2023-03-18)

* [field] Fix Bad adapter for NULL. (2f07867)

# 0.8.0rc10 (2023-03-17)

* [hop] Check that we are on hop_main branch before upgrade in prod. (7702aed)
* [model] Remove psycopg2.pool. (c7d99e3)
* [test] More coverage. (9d66be0)
* [test] Coverage (without half_orm/packager) still pre-alpha. (78edfd1)

# 0.8.0rc9 (2023-03-06)

* [CI][github] Test on push/pull request on default branch. (49e5db2)
* [relation] Relation methods are now prefixed with '_ho_'. (5e981f8)
* [test] Reenable fkeys test_runtime_error. (81a9446)
* [CI] Only set git user.email and user.name if in Github CI environment. (bc8aaee)
* [hop] Don't override global git user infos in dummy_test.py. (b8fc5cc)

# 0.8.0rc8 (2023-02-24)

* [Field] Register psycopg2 json adapter. (053d39e)
* [test] deprecated methods in relation. (7f96874)
* [gitlab][CI] Fix dependency. (3c6ad02)
* Add shields to README. (9446b35)
* [github][ci] OK. (b637929)
* [model] Fix annotation. (598570a)

# 0.8.0rc7 (2023-02-21)

* [model] Fix typo in deprecated message. (6b76f6e)

# 0.8.0rc6 (2023-02-16)

* [hop] Add release SQL files. (2a2b2d1)
* [relation] BREAKING CHANGE. Returning values must be specified except for ho_insert. (acf363e)
* [pipenv] Add pylint. (github/master) (035a589)
* [model] Config file load error management. (be281e9)
* [model] Fix deprecation warning on Python interpretor call. (30adfcc)

# 0.8.0rc5 (2023-02-08)

* Bump cryptography from 39.0.0 to 39.0.1 (5d5c200)
* [model] Add connection pool. (71f96fd)
* [model] Refactor. (274318c)
* [hop] Test script. (b85422c)
* [hop][WIP] Rename command test-release to apply-release. (71fdada)
* [hop][WIP] Use pytest as a module. (github/master) (69b0c55)
* [CI] Add superuser to root role (postgresql). (1f73a97)

# 0.8.0rc4 (2023-01-25)

* [hop][WIP] Add --devel option to hop new. (03b4750)
* [hop][halftest] Update to latest hop release. (cb73fb9)
* Fix a spelling mistake with below. (6659943)
* Remove pytest requirement from setup.py. (5ef9a13)
* [hop] Add git origin in .hop/config (a remote is no longer mandatory.) (0efe5d0)
* [relation] Prefix protected attributes of class Relation with _ho. (269f3e9)
* Add context information for deprectated methods. (9869e9b)

# 0.8.0rc3 (2023-01-20)

* [hop][WIP] Add pytest dependency (replace with unittest ?). (bdd52e8)
* Rename public and protected methods of half_orm.relation.Relation. (81c1084)

# 0.8.0rc2, hop 0.1.0a1 (2023-01-16)

* [hop][WIP] Integration of the hop command into half_orm. (d801ba5)

NOTE.
The hop command is a work in progress. It will replace the half_orm_packager package.

# 0.8.0rc1 (2023-01-04)

* [Fix] Foreign keys aliases were wrongly set as class attributes. (1de3c07)
* (relation) Remove code used to manage obsolete FKEYS variable. (393fccc)
* Upgrade dependencies. (ba1a202)

# 0.8.0rc0 (2022-12-07)

* Remove dependencies to pydash, click and gitpython (moved to half_orm_packager). (501549f)
* [field] Allow json and jsonb columns to receive python jsonifiable objects. (8da564f)
* Remove unnecessary select(). (d7b7722)
* (test) join. Add test_join_with_joined_object_with_FKEYS. (17948a8)
* (BREAKING CHANGE)(relation) Relation FKEYS module variable support is now removed (use Fkeys class attribute instead). (6ea7bd2)
* (BREAKING CHANGE)(relation) Relation.insert now returns a dict. (dffd6e3)
* [ci] Add Python 3.11. (origin/master, origin/HEAD, master) (72efc57)

## Breaking changes

* The `FKEYS` module variable is no longer supported. It is now replaced by the `Fkeys` class attribute.
* `Relation.insert` method only inserts one row and was returning a dict in a list. It now returns directly the dict:

  Before:
  ```py
  row_dict = MyTable(a='Something').insert()[0]
  ```
  Now:
  ```py
  row_dict = MyTable(a='Something').insert()
  ```

# 0.7.4 (2022-10-10)

* [relation] Add returning values to insert, update and delete. (816ae18)
* [relation] Return dict instead of RealDictRow. (fcbcbe0)
* [relation] Relation objects are now iterators. (143f0b0)
* Add half_orm.__version__. (60521cf)

# 0.7.3 (2022-09-21)

* [field][fix] Unsetting a Field by assigning None to it did not work anymore. (ef0735c)

# 0.7.2 (2022-09-21)

* Do not include partitioned tables in pg_meta. (04f6637)
* [doc][WIP] Add documentation in model and relation modules. (2040c95)
* [model] move relation class factory from relation to model. (eee6d05)
* [relation] Remove count method. (f3577c1)
* [model] get_relation_class raises MissingSchemaInName. (b3c9702)
* [model] Remove unused parameters dbname and raise_error from Model constructor. (95a3153)
* [docs][pg_meta][field][model][BREAKING CHANGE] Privatize some public methods. (a756443)

# 0.7.1 (2022-09-05)

* [relation] Allow fields names to be passed to Relation.get method. (93caa77)
* Add Model.execute_function and Model.call_procedure methods. (35215b3)
* Switch development status to beta. (74d3c67)
* [test] Don't reuse instances of Relation objects in tests. (0e137ce)
* [repr] Fix duplicates in unique constraints. Update README. (a91678e)

## New features

* You can now trigger the execution of PostgreSQL stored procedures and
functions by using `Model.execute_fonction` and `Model.call_procedure` methods.
* You can now pass fields names to The `Relation.get` method:
  ```py
  gaston = Person(last_name='Lagaffe', first_name='Gaston').get('id')
  ```

# 0.7.0 (2022-08-22)

* Fix Relation constraints representation. (c7beac7)
* Add deprecation warning for FKEYS module variable. (286a84c)
* [test] half_orm.hotest.hotAssertIsUnique takes a list of fields names. (283aefd)

## Breaking change

The `FKEYS` module variable (undocumented, mainly used with half_orm_packager) is
deprecated. It is replaced by the `Fkeys` Relation class attribute.

# 0.7.0-rc0 (2022-07-12)

* [doc] Improve README. (3363818)
* [WIP][fkeys] Make fkeys chaining possible. (62bf465)
* [fkeys][documentation] Add info about Fkeys class attribute in the relation class documentation. (0bc5af7)
* [WIP] Switch FKEYS module variable to Fkeys class attribute in halftest package (hop next release). (fb15769)
* [WIP] Allow constraint in joined objects. (61cd3f6)
* [test] Add tests for Relation._schemaname and Relation._relationname. (6845941)
* [relation][WIP] take into account the Fkeys attribute for a class inheriting from get_relation_class (00ecffe)
* [meta] Use tuple instead of normalized fqrn for key in metadata. (347fd98)

# 0.6.4 (2022-05-18)

* Use pg_meta qrn manipluation fonctions in relation and fkey modules. (45c9836)
* [test] Test Model._reload. (99f7c64)
* [model][meta] Move qrn manipulation fonctions to pg_meta. (29def79)
* [meta] Rename pg_metaview to pg_meta. (558d328)
* [meta] Remove Model._metadata attribute. (f2a68b3)

## Note

This release fixes some problems with half_orm_packager (pre-alpha).

# 0.6.3 (2022-05-17)

* [Fix] Regression in 0.6.2: dotted schema names were not handled properly. (0830a0c)

# 0.6.2 (2022-05-17) DO-NOT-USE

* [Fkeys] Fix insert, update and delete with constraints defined through foreign keys. (7bf9c77)
* [META] Change keys and fqrn to "<db>":"<schema>"."<relation>" (eada1b3)
* [CI] Build stage (4d836f2)
* [CI] Test from python 3.6 to 3.10 (ff3db37)

# 0.6.1 (2022-05-04)

* [Transaction] Fix #6. Autocommit mode stays at False on rollback. (643f500)

## Breaking change

There is a bug in the previous versions of the Transaction class.
If you use the Transaction class, **please upgrade to this release**.

# 0.5.14 (2022-05-04)

* [Transaction] Fix #6. Autocommit mode stays at False on rollback. (643f500)

## Breaking change

There is a bug in the previous versions of the Transaction class.
If you use the Transaction class, **please upgrade to this release**.

# 0.6.0 (2022-04-28)

* [Breaking change] Relation.join. (fdb4be8)
* [WIP] join on reverse fkeys. (73c3233)

## Breaking change

`Relation.join` now accepts either a string or a list of strings.

```
lagaffe.join((Post(), 'posts', ['id']))
```

now returns `[{'id': value1}, {'id': value2}, ...]` instead of `[value1, value2, ...]`. It must be replaced by:

```
lagaffe.join((Post(), 'posts', 'id'))
```

# 0.5.13 (2022-03-30)
* Fix singleton decorator (97dec7e)

# 0.5.12 (2022-03-30)
* Fix #4. Allow args for singleton decorator. (3a3085c)
* fix config file import when HALFORM_CONF_DIR is not absolute (0c54c10)

# 0.5.11 (2022-02-11)
* Add singleton decorator. (9b643cf)
* README: replace . (d075977)

# 0.5.10 (2022-02-08)
* [doc] Add return value on insert. (6a70c56)
* Add warning when trying to call a Field. (86243da)
* [CI] .gitlab-ci.yml. test stage. (364b823)
* Replace format with f strings. (c45463b)

# 0.5.9. (2021-12-01)
* Quote columns names in SQL update. (7056b98)

# 0.5.8. (2021-10-12)
* [model] Add attribute production. (6046432)

# 0.5.7 (2021-09-28)
* [relation] join: only format to string instances of classes listed in TO_PROCESS. (cc81112)
* [relation] join method now raises an exception if the relations are not connected. (9152506)

# 0.5.6. (2021-09-22)
* [relation] join method. (4dd6286)

# 0.5.5 (2021-09-07)
* Add Model.diconnect method. (70af38e)

# 0.5.4 (2021-09-04)
* Add support for partitioned tables. (9106143)
* [relation] _mogrify now triggers the print of the SQL query when a DML method is invoked. (0e66601)
* Add Relation.is_empty method (faster than len(relation) == 0). (08ec57a)

# 0.5.3 (2021-09-01)
* README. (ee2d453)
* Add model.has_relation method. (9490482)

# 0.5.2 (2021-08-26)
* [test] Add HoTest class (model testing). (319ddc2)
* [doc] README. (3b9dea1)

# 0.5.1 Fix wrong url in setup. (2021-07-27)

# 0.5.0 (2021-07-27)
* Remove dependency to .hop/config. (ebe7e71)
* Removal of hop (see halfORM_packager). (7311505)
* [test] Remove nose dependency. Add pytest (13226ea)

# 0.4.7 (2021-07-19)
* [hop][0.0.2] Adds placeholder for class attributes. (bbf2990)
* [module_template_1] Fix typo. (f1466ed)
* [pylint] Remove useless parameters in super. (882a795)
* [hop][pylint] Ignore invalid-name and attribute-defined-outside-init. (10ed373)
* [hop] Remove useless encoding in module_template_1. Put hop release in the first line. (8ab9b14)
* [hop] Fix No space allowed after bracket pylint(bad-whitespace). (bae786b)
* [fkey] Use a sorted list in repr for the referenced columns of a foreign key. (21024cd)

# 0.4.6 (2021-07-08)
* [fkey] Add missing quotes in fields names. (2ff4f5d)
* [test] Replace FKEYS_PROPERTIES by FKEYS (e09ac10). (3c0a6a0)

# 0.4.5 (2021-06-22)
* [hop] hop update - fix warning message in generated files (c048cda)
* [hop] Fix local variable 'model' referenced before assignment. (09ee493)
* [hop] Add hop release in modules. Fix missing warning. (5976ddb)
* [init] if project config does not exist, asks for config creation (6132158)
* [model] Model can be instantiated even if there's no ".hop/config" file, (a1e3cf6)
* [hop][create] fix case when config file already exists but db is not yet created (59bc901)
* [hop][create] Fix ident login (7866b25)
* [hop][breaking] Replace "argparse" with "click". We now use "commands" instead of options : (6a3729f)
* [model] Remove default value for "config_file" (seems to be used all the time) (e8103b5)
* [scripts] set script to half_orm.hop.__init__:main (more precise than before) (b7bbc83)
* [setup.py] set __version__ in half_orm/__init__.py (to use it in hop -v) (a622abc)
* [deps] add click dependency (91684a3)
* [deps] missing dependency : pyYaml (f30cbbf)
* [pipfile] fix deps psycopg2 (fe2bba2)
* [patch][wip] Add missing penultimate_release view. (503816a)
* [patch] Ignore path with uppercase in first letter. (9989913)
* [fix] order in meta.view.last_release (6826178)
* [hop] Add init patch system. (e45e4f4)
* [hop] Skip camel case directories. (f186f06)


# 0.4.4 (2021-05-20)
* [hop][test] Fix wrong reference to package. (2a6a222)
* [hop] Adds a base_test module to the package. (5a27678)
* [hop] Fix error on create. (be4d3ff)

# 0.4.3 (2021-05-11)
* [hop] Add -i argument (ignore-tests) (6559244)
* [hop] Add basic testing. (14db2a0)

# 0.4.2 (2021-05-10)
* [hop/fkeys] Fix missing comma. FKEYS_PROPERTIES is deprecated. Ignore empty strings. (e09ac10)

# 0.4.1 (2021-05-10)
* [hop] Add FKEYS_PROPERTIES template. (131b529)
* Update license/setup. (aaa86dd)
* [hop/patch] Adds Patch class. (e95ca0f)
* [0.4.0] adding Pipfile to the hop package. (95dedf1)
* [setup] Fix missing hop package. (57111e1)
* [hop] Add release number to First release. (dc1056e)
* [Pipfile] Add coverage dev dependency. (2df7273)
* [hop] remove dead code. (c0420dd)
* [hop] Creates connection config file and database if missing. (5327ec3)
* [hop] Adds main/master and devel branches on create. (6a6b4e4)
* [hop] Generates skeleton test files. (b002cc8)
* [hop] Add date to meta.release. (9927a29)
* [hop] Add git project on init. (9f39516)
* [hop] Add patch system to hop. (b24ffd6)
* [0.3.1] new release. (9db30db)
* [template] setup.py README.rst -> README.md. (d7a8c69)
* [wip] Add patch system to the hop command. (0734f5d)
* [hop] Take into account HALFORM_CONF_DIR env variable. (49593e0)
* [relation] Remove None values from update kwargs. (8652909)
* Update CHANGELOG. (ef392a7)

# 0.3 (2020-11-15)

## Features

* Automatic attempt to reconnect to DB in case of execution failure. (2fd8f6d)
* Allow connection with only the database name. (325f712)
* Add HALFORM_CONF_DIR environment variable (defaults to /etc/half_orm). (45e3431)
* Prevent update and test package when creating the package with hop -c. (153cbf6)
* Allow None as a legit value to unset a field. (eb13677)
* hop renames README.rst to README.md and .haflORM to .hop. (307591c)
* Add usage information into the README file generated by hop. (c956339)
* Improve README in the package generated by hop. (00c3743)

## Fixes

* relation.is_set must always retrun a boolean. (942da6c)
* Typos in README. (0caba1c)
* Fix broken unaccent in relation. (9c3d910)

## Breaking Changes

* hop now generates a .hop directory in the package instead of .halfORM. (588c2bf)

# 0.2 (2020-04-29)

## Features

- Columns of a relation are now regular attributs of the Relation class.
  This is a breaking change.
- no more need to install halftest package (pip3) to test half_orm.
- with context on a relation now enters a transaction.

## Bug fixes

- allow weird column names: `a = 1` is a regular column name in PostgreSQL.
  Of course, you can't use the doted notation to handle such column with
  half_orm. Instead, use `rel.__dict__['a = 1']`.
- reverse fkeys

## Breaking Changes

- Relation class is not inheriting from OrderedDict anymore.
  If `rel` is a Relation object, `rel['col']` must be replaced by `rel.col`.
- A Relation object `rel` is frozen after initialisation (`__init__`),
  meaning you can't add attributes to it. This is to prevent errors due
  to typos in the expression `rel.col = 'a'` vs. `rel.cal = 'a'`. If
  `cal` column doesn't exist in the relation, an exception is raised.
  If you need to add an attribute to a class inheriting from Relation,
  you can use `_ho_unfreeze` and `_ho_freeze` methods.

# 0.1.0-alpha.7 (2016-11-29)

## Features

- **relation:** Inherit foreign keys. (acb51ba)
- **test:** Add halftest package. (f2d91af)
- **model, relation:** Add reverse foreign keys. (50edf5f)
- **relation:** cast method now returns the casted relation. (bbde48a)
- **relation:** Add order_by select parameter. (57791c7)

## Bug fixes

- **fkeys:** Use issubclass instead of hasattr. (2aaf58e)
- **relation, fkey:** Fix relations with multiple foreign keys. (1a69e16)

# 0.1.0-alpha.6 (2016-11-25)

## Bug fixes

- **relation:** Refactoring. Fix fkeys on relation with set operations. Need tests. (bd806f3)
- **relation:** Check if right obj is None in \_\_set__op__. (4cf0b6a)
- **relation:** \_\_neg__ now uses \_\_set__op__ method. (444763c)
- **relation:** Pass the comparison operator with the value in to_dict method. (67e8724)
- **test:** Universe and empty sets are now correctly defined (1 = 1 patch). (2babe1f)

# 0.1.0-alpha.5 (2016-11-22)

## Features

- **halfORM:** Catch error if there is some wierd inheritance in PG that Python MRO can't handle. (aa9543e)
- **field:** Replace \_set_value method by set.
- **relation:** The ugly yet very useful 1 = 1 patch. (fd3d06f)
- **fkey:** Refactoring. Reverse key is now named after the relation it references. (5b98194)

## Bug fixes

- **relation:** Disambiguation of column name when using SQL join request.Disambiguation of column name when using SQL join request. (25f9a48)
- **halfORM:** Fix typo in module_template_1. (664159b)
- **relation:** Fix bug with FKEYS_PROPERTIES and inheritance. (675171f)
- **relation:** count must use distinct. (d6ac16b)
- **relation:** Fix joins with set operators. (e4c885c)

# 0.1.0-alpha.4 (2016-11-14)

## Features

- **halfORM:** Reduce to two the spaces reserved to the developper in relation modules (85c3d6c, 0cd6d5f)
- **model:** raise_error parameter is now passed to \_connect/reconnect. (6bba6dd)
- **relation:** Add attribute \_qrn (<schema name>.<relation name>) without double quotes. (fd6c07d)
- **relation:** Add \_set_fkeys_properties. (2b0335f)

## Bug fixes

- **halfORM:** Reverse the order in inheritance. (d7d4432)
- **halfORM:** Use aliases for imported inherited classes. Add warning in every modules. (e1f9841)

# 0.1.0-alpha.3 (2016-11-12)

## Features

- **Relation:** Add a cast method to cast to another relation type. (d662ccd)
- **halfORM:** The script can now be called without argument inside a half_orm package. (95a4ba0)
- **Model:** Model.relation replaced by get_relation_class now returns a class. (0998253)
- **Relation:** \_\_str__ becomes \_\_repr__. (af6498b)

## Bug fixes

- **halfORM:** Fix problem with curly braces in user's code. (7a02309)
- **Fkey:** The FK now references the class in the good scope. (fc304c7)
- **Relation:** Use field.where_repr to have a correct construct of the request with fkeys. (39116a2)
- **Relation:** remove the display of FOREIGN KEY when there is no FK. (89d9c6b)

# 0.1.0-alpha.2 (2016-11-10)

## Features

- **Fkey:** Add tests for foreign keys. (5158ece)
- **Relation:** attributes fields and fkeys are renamed \_fields and \_fkeys. (2e29af0)
- **Relation:** mogrify is renamed to \_mogrify. (3f3541f)

## Bug fixes

- **Fkey:** Fix bug in fkey introduced in 3c248a29 by fqrn renaming. (5158ece)
- **Fkey:** Fix is_set pb with fkeys and not constrained relations. (1c6e7d9)
- **Relation:** len wasn't working since Fields introduction. (2e29af0)
- **Relation:** Fix pb with isinstance and Relation objects. (51ff1db)

# 0.1.0-alpha.1 (2016-11-08)

- First alpha release
