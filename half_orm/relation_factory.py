"This module provides the factory function"

import sys
from functools import wraps

from half_orm import pg_meta
from half_orm import model_errors
from half_orm import utils
from half_orm.relation import Relation, REL_CLASS_NAMES

def factory(dct):
    """Factory function that generates a `Relation` subclass corresponding to a PostgreSQL relation.

    Args:
        dct (dict): a dictionary containing the following keys:
            - 'fqrn' (tuple): a fully qualified relation name, which is a tuple of 3 strings:
                the database name, the schema name and the relation name.
            - 'model' (Model): an instance of the `Model` class representing the database model.

    Returns:
        A `Relation` subclass that corresponds to the specified PostgreSQL relation.
        The class name is generated using the database name, the schema name and the relation name,
        and it inherits from the `Relation` class.

    Raises:
        UnknownRelationError: if the specified relation does not exist in the database.
    """
    def _gen_class_name(rel_kind, sfqrn):
        """Generates class name from relation kind and FQRN tuple"""
        class_name = "".join([elt.capitalize() for elt in
                            [elt.replace('.', '') for elt in sfqrn]])
        return f"{rel_kind}_{class_name}"

    bases = [Relation,]
    tbl_attr = {}
    tbl_attr['_ho_fkeys_properties'] = False
    tbl_attr['_qrn'] = pg_meta.normalize_qrn(dct['fqrn'])

    tbl_attr.update(dict(zip(['_dbname', '_schemaname', '_relationname'], dct['fqrn'])))
    model = dct['model']
    model._classes_.setdefault(tbl_attr['_dbname'], {})
    tbl_attr['_ho_model'] = model
    dbname, schema, relation = dct['fqrn']
    rel_class = None
    if model._classes_.get(dbname):
        rel_class = model._classes_[dbname].get((dbname, schema, relation))
    if not rel_class:
        try:
            metadata = model._relation_metadata(dct['fqrn'])
        except KeyError as exc:
            raise model_errors.UnknownRelation(dct['fqrn']) from exc
        if metadata['inherits']:
            metadata['inherits'].sort()
            bases = []
        for parent_fqrn in metadata['inherits']:
            bases.append(factory({'fqrn': parent_fqrn, 'model': model}))
        tbl_attr['_ho_metadata'] = metadata
        tbl_attr['_t_fqrn'] = dct['fqrn']
        tbl_attr['_fqrn'] = pg_meta.normalize_fqrn(dct['fqrn'])
        tbl_attr['_ho_kind'] = REL_CLASS_NAMES[metadata['tablekind']]
        class_name = _gen_class_name(REL_CLASS_NAMES[metadata['tablekind']], dct['fqrn'])
        rel_class = type(class_name, tuple(bases), tbl_attr)
        model._classes_[tbl_attr['_dbname']][dct['fqrn']] = rel_class
    return rel_class
