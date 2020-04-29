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
  you can use `_unfreeze` and `_freeze` methods.

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
