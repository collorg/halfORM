#-*- coding: utf-8 -*-
# pylint: disable=protected-access

"""This module provides: relation, RelationFactory

The relation function allows you to directly instanciate a Relation object
given its fully qualified relation name:
- relation(<FQRN>)

The RelationFactory can be used to create classes to manipulate the relations
of the database:
```
class MyClass(metaclass=RelationFactory):
    fqrn = '<FQRN>'
```

About QRN and FQRN:
- FQRN stands for: Fully Qualified Relation Name. It is composed of:
  <database name>.<schema name>.<table name>.
  Only the schema name can have dots in it.
- QRN is the Qualified Relation Name. Same as the FQRN without the database
  name.

Double quotes can be ommited even if there are dots in the schema name for
both FQRN and QRN. The _normalize_fqrn and _normalize_qrn functions add
the double quotes.
"""

import sys
from halfORM import relation_errors
from halfORM.transaction import Transaction

#### THE following METHODS are included in Relation class according to
#### relation type (Table or View). See TABLE_INTERFACE and VIEW_INTERFACE.

def __init__(self, **kwargs):
    self.__cursor = self.model.connection.cursor()
    self.__cons_fields = []
    attr = self.__getattribute__
    _ = [attr(field_name).set(value) for field_name, value in kwargs.items()]
    self.__deja_vu_join = []
    self.__joined_to = []
    self.__in_join = [(self, None)]
    self.__sql_query = []
    self.__sql_values = []

def __call__(self, **kwargs):
    """__call__ method for the class Relation

    Instanciate a new object with all fields unset.
    """
    return relation(self.__fqrn, **kwargs)

def json(self, **kwargs):
    """Returns a JSON representation of the set returned by the select query.
    """
    import json as js_, time
    def handler(obj):
        """Replacement of default handler for json.dumps."""
        if hasattr(obj, 'timetuple'):
            # seconds since the epoch
            return int(time.mktime(obj.timetuple()))
        #elif isinstance(obj, ...):
        #    return ...
        else:
            raise TypeError(
                'Object of type {} with value of '
                '{} is not JSON serializable'.format(type(obj), repr(obj)))
    return js_.dumps([elt for elt in self.select(**kwargs)], default=handler)

def __repr__(self):
    rel_kind = self.__kind
    ret = []
    ret.append("{}: {}".format(rel_kind.upper(), self.__fqrn))
    if self.__metadata['description']:
        ret.append("DESCRIPTION:\n{}".format(self.__metadata['description']))
    ret.append('FIELDS:')
    mx_fld_n_len = 0
    for field in self.__fields:
        if len(field.name) > mx_fld_n_len:
            mx_fld_n_len = len(field.name)
    for field in self.__fields:
        ret.append('- {}:{}{}'.format(
            field.name,
            ' ' * (mx_fld_n_len + 1 - len(field.name)),
            repr(field)))
    if self.__fkeys:
        plur = len(self.__fkeys) > 1 and  'S' or ''
        ret.append('FOREIGN KEY{}:'.format(plur))
        for fkey in self.__fkeys:
            ret.append(repr(fkey))
    return '\n'.join(ret)

@property
def fqrn(self):
    """Returns the FQRN (fully qualified relation name)"""
    return self.__fqrn

@property
def is_set(self):
    """return True if one field at least is set"""
    for field in self.__fields:
        if field.is_set:
            return True
    return False

@property
def fields(self):
    """Yields the fields of the relation."""
    for field in self.__fields:
        yield field

def __get_set_fields(self):
    """Retruns a list containing only the fields that are set."""
    return [field for field in self.__fields if field.is_set]

def join(self, frel, fkey_name=None):
    """Returns the foreign relation constained by self.
    """
    def __join_match_fkeys(self, fqrn, fkey_name):
        """Returns the list of keys matchin fqrn."""
        if not fkey_name:
            ret_val = [fkey for fkey in self.__fkeys if fkey.fk_fqrn == fqrn]
            return ret_val
        else:
            return [fkey for fkey in self.__fkeys if fkey.name == fkey_name]
    if isinstance(frel, str):
        # Assume frel is a QRN
        frel = self.model.relation(frel)
    # Search for direct or reversed keys to join on.
    fkeys_dir = __join_match_fkeys(self, frel.fqrn, fkey_name)
    fkeys_rev = __join_match_fkeys(frel, self.fqrn, fkey_name)
    if fkeys_dir and fkeys_rev:
        raise Exception("Cycle")
    elif len(fkeys_rev) == 0 and len(fkeys_dir) != 1:
        raise Exception("More than one direct fkey matching")
    elif len(fkeys_dir) == 0 and len(fkeys_rev) != 1:
        raise Exception("More than one reverse fkey matching")
    if fkeys_dir:
        fkey = self.__getattribute__(fkeys_dir[0].name)
        fkey.set(self, frel)
    else:
        fkey = fkeys_rev[0]
        fkey.set(frel, self)
    frel.__joined_to.insert(0, (self, fkey))
    frel.__in_join = self.__in_join
    frel.__in_join.append((self, fkey))
    return frel

def __get_from(self, orig_rel=None, deja_vu=None):
    """Constructs the __sql_query and gets the __sql_values for self."""
    def __sql_id(rel):
        """Returns the FQRN as alias for the sql query."""
        return "{} as r{}".format(rel.fqrn, id(rel))

    if deja_vu is None:
        orig_rel = self
        self.__sql_query = [__sql_id(self)]
        deja_vu = [(self, None)]
    for elt, fkey in self.__joined_to:
        if (elt, fkey) in deja_vu or elt is orig_rel:
            sys.stderr.write("déjà vu in from! {}\n".format(elt.fqrn))
            continue
        deja_vu.append((elt, fkey))
        from_ = elt
        if fkey.frel is elt:
            from_ = fkey.from_
        elt.__get_from(orig_rel, deja_vu)
        elt.__sql_query, elt.__sql_values = fkey.join_query(from_)
        orig_rel.__sql_query.insert(1, 'join {} on'.format(__sql_id(elt)))
        orig_rel.__sql_query.insert(2, elt.__sql_query)
        if orig_rel != elt:
            orig_rel.__sql_values = (elt.__sql_values + orig_rel.__sql_values)

def __select_args(self, *args, **kwargs):
    """Returns the what, where and values needed to construct the queries.
    """
    id_ = 'r{}'.format(id(self))
    def praf(field_name):
        """Returns field_name prefixed with relation alias."""
        if kwargs['__query'] == 'select':
            return '{}.{}'.format(id_, field_name)
        return field_name
    attr = self.__getattribute__
    what = praf('*')
    if args:
        what = ', '.join([praf(attr(field_name).name) for field_name in args])
    values = []
    set_fields = self.__get_set_fields()
    where = ''
    if set_fields:
        where = [
            '{} {} %s'.format(
                praf(field.name), field.comp) for field in set_fields]
        where = 'where {}'.format(" and ".join(where))
        values = [field.value for field in set_fields]
    return what, where, values

def __get_query(self, query_template, *args, **kwargs):
    self.__sql_values = []
    what, where, values = self.__select_args(*args, __query='select', **kwargs)
    self.__get_from()
    return (
        query_template.format(what, ' '.join(self.__sql_query), where), values)

def select(self, *args, **kwargs):
    """Generator. Yiels the result of the query as a dictionary.

    - @args are fields names to restrict the returned attributes
    - @kwargs: limit, order by, distinct... options
    """
    self.__sql_values = []
    query_template = "select {} from {} {}"
    query, values = self.__get_query(query_template, *args, **kwargs)
    try:
        self.__cursor.execute(query, tuple(self.__sql_values + values))
    except Exception as err:
        print(self.__cursor.mogrify(
            query, tuple(self.__sql_values + values)).decode('utf-8'))
        raise err
    for elt in self.__cursor.fetchall():
        yield elt

def get(self, **kwargs):
    """Yields instanciated Relation objects instead of dict."""
    for dct in self.select(**kwargs):
        yield self(**dct)

def getone(self):
    """Returns the Relation object extracted.

    Raises an exception if no or more than one element is found.
    """
    count = len(self)
    if count != 1:
        raise relation_errors.ExpectedOneError(self, count)
    return list(self.get())[0]

def __len__(self, *args, **kwargs):
    """Retruns the number of tuples matching the intention in the relation.

    See select for arguments.
    """
    query_template = "select count({}) from {} {}"
    query, values = self.__get_query(query_template, *args, **kwargs)
    try:
        self.__cursor.execute(query, tuple(self.__sql_values + values))
    except Exception as err:
        print(self.__cursor.mogrify(
            query, tuple(self.__sql_values + values)).decode('utf-8'))
        raise err
    return self.__cursor.fetchone()['count']

def __update_args(self, **kwargs):
    """Returns the what, where an values for the update query."""
    what_fields = []
    new_values = []
    _, where, values = self.__select_args(__query='update')
    for field_name, new_value in kwargs.items():
        what_fields.append(field_name)
        new_values.append(new_value)
    what = ", ".join(["{} = %s".format(elt) for elt in what_fields])
    return what, where, new_values + values

def update(self, no_clause=False, **kwargs):
    """
    kwargs represents the values to be updated {[field name:value]}
    The object self must be set unless no_clause is false.
    """
    if not kwargs:
        return # no new value update. Should we raise an error here?
    assert self.is_set or no_clause

    query_template = "update {} set {} {}"
    what, where, values = self.__update_args(**kwargs)
    query = query_template.format(self.__fqrn, what, where)
    self.__cursor.execute(query, tuple(values))

def __what_to_insert(self):
    """Returns the field names and values to be inserted."""
    fields_names = []
    values = ()
    set_fields = self.__get_set_fields()
    if set_fields:
        fields_names = [field.name for field in set_fields]
        values = [field.value for field in set_fields]
    return ", ".join(fields_names), values

def insert(self):
    """Insert a new tuple into the Relation."""
    query_template = "insert into {} ({}) values ({})"
    fields_names, values = self.__what_to_insert()
    what_to_insert = ", ".join(["%s" for i in range(len(values))])
    query = query_template.format(self.__fqrn, fields_names, what_to_insert)
    self.__cursor.execute(query, tuple(values))

def delete(self, no_clause=False, **kwargs):
    """Removes a set of tuples from the relation.
    kwargs is {[field name:value]}
    To empty the relation, no_clause must be set to True.
    """
    attr = self.__getattribute__
    _ = [attr(field_name).set(value) for field_name, value in kwargs.items()]
    assert self.is_set or no_clause
    query_template = "delete from {} {}"
    _, where, values = self.__select_args(__query='delete')
    query = query_template.format(self.__fqrn, where)
    self.__cursor.execute(query, tuple(values))

def __getitem__(self, key):
    return self.__cursor.fetchall()[key]

transaction = Transaction

#### END of Relation methods definition

TABLE_INTERFACE = {
    # shared with view_interface

    '__init__': __init__,
    '__call__': __call__,
    '__getitem__': __getitem__,
    '__get_set_fields': __get_set_fields,
    '__repr__': __repr__,
    'json': json,
    'fields': fields,
    '__get_from': __get_from,
    '__get_query': __get_query,
    'fqrn': fqrn,
    'is_set': is_set,
    '__select_args': __select_args,
    'select': select,
    '__len__': __len__,
    'get': get,
    'getone': getone,

    # specific table

    'insert': insert,
    '__what_to_insert': __what_to_insert,
    'update': update,
    '__update_args': __update_args,
    'delete': delete,
    'transaction': transaction,
    'join': join,
}

VIEW_INTERFACE = {
    '__init__': __init__,
    '__call__': __call__,
    '__getitem__': __getitem__,
    '__get_set_fields': __get_set_fields,
    '__repr__': __repr__,
    'json': json,
    'fields': fields,
    '__get_from': __get_from,
    '__get_query': __get_query,
    'fqrn': fqrn,
    'is_set': is_set,
    '__select_args': __select_args,
    'select': select,
    '__len__': __len__,
    'get': get,
    'getone': getone,
}

class Relation():
    """Base class of Table and View classes (see RelationFactory)."""
    pass

class RelationFactory(type):
    """RelationFactory Metaclass
    """
    def __new__(mcs, class_name, bases, dct):
        from halfORM import model, model_errors
        def _gen_class_name(rel_kind, sfqrn):
            """Generates class name from relation kind and FQRN tuple"""
            class_name = "".join([elt.capitalize() for elt in
                                  [elt.replace('.', '') for elt in sfqrn]])
            return "{}_{}".format(rel_kind, class_name)

        #TODO get bases from table inheritance
        bases = (Relation,)
        rf_ = RelationFactory
        tbl_attr = {}
        tbl_attr['__fqrn'], sfqrn = _normalize_fqrn(dct['fqrn'])
        attr_names = ['dbname', 'schemaname', 'relationname']
        for i in range(len(attr_names)):
            tbl_attr[attr_names[i]] = sfqrn[i]
        dbname = tbl_attr['dbname']
        tbl_attr['model'] = model.Model.deja_vu(dbname)
        if not tbl_attr['model']:
            tbl_attr['model'] = model.Model(dbname)
        try:
            metadata = tbl_attr['model'].metadata['byname'][tuple(sfqrn)]
        except KeyError:
            raise model_errors.UnknownRelation(sfqrn)
        tbl_attr['__metadata'] = metadata
        if dct.get('model'):
            tbl_attr['model'] = dct['model']
        tbl_attr['__sfqrn'] = tuple(sfqrn)
        rel_class_names = {'r': 'Table', 'v': 'View'}
        kind = metadata['tablekind']
        tbl_attr['__kind'] = rel_class_names[kind]
        rel_interfaces = {'r': TABLE_INTERFACE, 'v': VIEW_INTERFACE}
        rf_.__set_fields(tbl_attr)
        for fct_name, fct in rel_interfaces[kind].items():
            tbl_attr[fct_name] = fct
        class_name = _gen_class_name(rel_class_names[kind], sfqrn)
        return super(rf_, mcs).__new__(mcs, class_name, (bases), tbl_attr)

    @staticmethod
    def __set_fields(ta_):
        """ta_: table attributes dictionary."""
        from .field import Field
        from .fkey import FKey
        ta_['__fields'] = []
        ta_['__fkeys'] = []
        dbm = ta_['model'].metadata
        flds = list(dbm['byname'][ta_['__sfqrn']]['fields'].keys())
        for field_name, f_metadata in dbm['byname'][
                ta_['__sfqrn']]['fields'].items():
            ta_[field_name] = Field(field_name, f_metadata)
            ta_['__fields'].append(ta_[field_name])
        for field_name, f_metadata in dbm['byname'][
                ta_['__sfqrn']]['fields'].items():
            fkeyname = f_metadata.get('fkeyname')
            if fkeyname and not fkeyname in ta_:
                ft_ = dbm['byid'][f_metadata['fkeytableid']]
                ft_sfqrn = ft_['sfqrn']
                fields_names = [flds[elt-1]
                                for elt in f_metadata['keynum']]
                ft_fields_names = [ft_['fields'][elt]
                                   for elt in f_metadata['fkeynum']]
                ta_[fkeyname] = FKey(
                    fkeyname, ft_sfqrn, ft_fields_names, fields_names)
                ta_['__fkeys'].append(ta_[fkeyname])

def relation(_fqrn, **kwargs):
    """This function is used to instanciate a Relation object using
    its FQRN (Fully qualified relation name):
    <database name>.<schema name>.<relation name>.
    If the <schema name> comprises a dot it must be enclosed in double
    quotes. Dots are not allowed in <database name> and <relation name>.
    """
    return RelationFactory(None, None, {'fqrn': _fqrn})(**kwargs)

def _normalize_fqrn(fqrn):
    """
    Transform <db name>.<schema name>.<table name> in
    "<db name>"."<schema name>"."<table name>".
    Dots are allowed only in the schema name.
    """
    fqrn = fqrn.replace('"', '')
    dbname, schema_table = fqrn.split('.', 1)
    schemaname, tablename = schema_table.rsplit('.', 1)
    sfqrn = (dbname, schemaname, tablename)
    return '"{}"."{}"."{}"'.format(*sfqrn), sfqrn

def _normalize_qrn(qrn):
    """
    qrn is the qualified relation name (<schema name>.<talbe name>)
    A schema name can have any number of dots in it.
    A table name can't have a dot in it.
    returns "<schema name>"."<relation name>"
    """
    return '.'.join(['"{}"'.format(elt) for elt in qrn.rsplit('.', 1)])
