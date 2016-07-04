#-*- coding: utf-8 -*-
# pylint: disable=protected-access, too-few-public-methods

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

import datetime
import sys
import uuid
import yaml
from collections import OrderedDict
from copy import copy
from halfORM import relation_errors
from halfORM.transaction import Transaction

class UnknownAttributeError(Exception):
    def __init__(self, msg):
        super(self.__class__, self).__init__(
            "ERROR! Unknown attribute: {}.".format(msg))

class ExpectedOneElementError(Exception):
    def __init__(self):
        super(self.__class__, self).__init__(
            "ERROR! More than one element for a non list item.")

class SetOp(object):
    ### WARNING! NOT FUNCTIONAL!
    """SetOp class stores the set operations made on the Relation class objects
    in a tree like structure.
    - __op is one of {'or', 'and', 'sub', 'neg'}
    - __right is a Relation object. It can be None if the operator is 'neg'.
    """
    def __init__(self):
        self.__neg = False
        self.__op = []

    @property
    def op_(self):
        """Poperty retruning the __op value."""
        return self.__op

    def is_set(self):
        """Return True if the self object has been set."""
        return self.__op != []

    def add(self, left, op_, right):
        """Add the informations corresponding to the new op."""
        self.__op.append(
            (op_,
            left.set_ops.__op and left.set_ops or left,
            right.set_ops.__op and right.set_ops or right))

    def __get_neg(self):
        """returns the value of self.__neg."""
        return self.__neg
    def __set_neg(self, neg):
        """sets the value of self.__neg. The neg argument is not used."""
        self.__neg = neg
    neg = property(__get_neg, __set_neg)

    def __iter__(self):
        def iter(set_op):
            """Recursive method used to iterate over set_op."""
            for op_, left, right in set_op.__op:
                if isinstance(left, SetOp):
                    for op_, left, right in iter(left.__op):
                        yield op_, left, right
                if isinstance(right, SetOp):
                    for op_, left, right in iter(right):
                        yield op_, left, right
                else:
                    yield op_, left, right
        for op_, left, right in iter(self):
            yield op_, left, right

    def __repr__(self):
        #for op, left, right in self:
        #    output.append("{} ({},\n{})".format(op, left, right))
        return str(self.__op)

class SQLClause(object):
    def __init__(self):
        self.__order_by = []
        self.__offset = None
        self.__limit = None

class Relation(object):
    """Base class of Table and View classes (see RelationFactory)."""
    pass

#### THE following METHODS are included in Relation class according to
#### relation type (Table or View). See TABLE_INTERFACE and VIEW_INTERFACE.

def __init__(self, **kwargs):
    self.__cursor = self.model.connection.cursor()
    self.__cons_fields = []
    kk = set(kwargs.keys())
    try:
        assert kk.intersection(self._fields_names) == kk
    except:
        raise UnknownAttributeError(str(kk.difference(self._fields_names)))
    _ = {self.__setattr__(field_name, value)
         for field_name, value in kwargs.items()}
    self._joined_to = []
    self.__query = None
    self.__sql_query = []
    self.__sql_values = []
    self.__mogrify = False
    self.__set_ops_tree = SetOp()
    _ = {field._set_relation(self) for field in self._fields}

@property
def set_ops(self):
    return self.__set_ops_tree

def __call__(self, **kwargs):
    return relation(self.__fqrn, **kwargs)

def group_by(self, data, directive):
    def inner_group_by(data, directive, grouped_data, gdata_tree, gdata=None):
        if gdata is None:
            directive = yaml.safe_load(directive)
            gdata = grouped_data
        directive_type = type(directive)
        is_list = type(directive) == list
        if directive_type is list:
            directive = directive[0]
        keys = [key for key in directive.keys()]
        for elt in data:
            res_elt = {}
            for key in keys:
                value = directive[key]
                if type(value) in [list, dict]:
                    group_name = key
                    if gdata.get(key) is None:
                        gdata[key] = type(value)()
                    gdata_tree.append(gdata[key])
                    inner_group_by([elt], value, grouped_data, gdata_tree, gdata_tree[-1])
                    gdata_tree.pop()
                else:
                    try:
                        res_elt.update({value:elt[key]})
                    except:
                        raise UnknownAttributeError(key)
            if type(gdata) is dict:
                for key in res_elt:
                    if gdata.get(key):
                        try:
                            assert res_elt[key] == gdata[key]
                        except:
                            raise ExpectedOneElementError()
                gdata.update(res_elt)
            else:
                if not res_elt in gdata:
                    gdata.append(res_elt)

    grouped_data = {}
    gdata_tree = []
    inner_group_by(data, directive, grouped_data, gdata_tree)
    return grouped_data

def to_json(self, group_by_directive=None, **kwargs):
    """Returns a JSON representation of the set returned by the select query.
    """
    import json
    import time

    def handler(obj):
        """Replacement of default handler for json.dumps."""
        if hasattr(obj, 'timetuple'):
            # seconds since the epoch
            return int(time.mktime(obj.timetuple())) * 1000
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, datetime.timedelta):
            return str(obj)
        else:
            raise TypeError(
                'Object of type {} with value of '
                '{} is not JSON serializable'.format(type(obj), repr(obj)))

    res = [elt for elt in self.select(**kwargs)]
    if group_by_directive:
        res = self.group_by(res, group_by_directive)
    return json.dumps(res, default=handler)

def __repr__(self):
    rel_kind = self.__kind
    ret = []
    ret.append("{}: {}".format(rel_kind.upper(), self.__fqrn))
    if self.__metadata['description']:
        ret.append("DESCRIPTION:\n{}".format(self.__metadata['description']))
    ret.append('FIELDS:')
    mx_fld_n_len = 0
    for field in self._fields:
        if len(field.name()) > mx_fld_n_len:
            mx_fld_n_len = len(field.name())
    for field in self._fields:
        ret.append('- {}:{}{}'.format(
            field.name(),
            ' ' * (mx_fld_n_len + 1 - len(field.name())),
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

def is_set(self):
    """Return True if one field at least is set or if self has been
    constrained by at least one of its foreign keys or self is the
    result of a combination of Relations (using set operators).
    """
    return (bool(self._joined_to) or
            self.__set_ops_tree.is_set() or
            bool({field for field in self._fields if field.is_set()}))

@property
def fields(self):
    """Yields the fields of the relation."""
    for field in self._fields:
        yield field

def __get_set_fields(self):
    """Retruns a list containing only the fields that are set."""
    return [field for field in self._fields if field.is_set()]

def __join_query(self, fkey, op_=' and '):
    """Returns the join_query, join_values of a foreign key.
    fkey interface: frel, from_, to_, fields, fk_names
    """
    from_ = self
    if fkey.to_ is self or from_ is None:
        from_ = fkey.from_
    to_ = fkey.to_
    assert id(from_) != id(to_)
    to_id = 'r{}'.format(id(to_))
    from_id = 'r{}'.format(id(from_))
    from_fields = ('{}.{}'.format(from_id, name)
                   for name in fkey.fields)
    to_fields = ('{}.{}'.format(to_id, name) for name in fkey.fk_names)
    bounds = op_.join(['{} = {}'.format(a, b) for
                       a, b in zip(to_fields, from_fields)])
    constraints_to_query = [
        '{}.{} {} %s'.format(to_id, field.name(), field.comp())
        for field in to_.fields if field.is_set()]
    constraints_to_values = (
        field for field in to_.fields if field.is_set())
    constraints_from_query = [
        '{}.{} {} %s'.format(from_id, field.name(), field.comp())
        for field in from_.fields if field.is_set()]
    constraints_from_values = (
        field for field in from_.fields if field.is_set())
    constraints_query = op_.join(
        constraints_to_query + constraints_from_query)
    constraints_values = list(constraints_to_values) + list(constraints_from_values)

    if constraints_query:
        bounds = op_.join([bounds, constraints_query])
    return str(bounds), constraints_values

def __get_from(self, orig_rel=None, deja_vu=None):
    """Constructs the __sql_query and gets the __sql_values for self."""
    def __sql_id(rel):
        """Returns the FQRN as alias for the sql query."""
        return "{} as r{}".format(rel.fqrn, id(rel))

    if deja_vu is None:
        orig_rel = self
        self.__sql_query = [__sql_id(self)]
        deja_vu = {id(self):[(self, None)]}
    for rel, fkey in self._joined_to:
        id_rel = id(rel)
        new_rel = id_rel not in deja_vu
        if new_rel:
            deja_vu[id_rel] = []
        elif (rel, fkey) in deja_vu[id_rel] or rel is orig_rel:
            #sys.stderr.write("déjà vu in from! {}\n".format(rel.fqrn))
            continue
        deja_vu[id_rel].append((rel, fkey))
        rel.__get_from(orig_rel, deja_vu)
        rel.__sql_query, rel.__sql_values = rel.__join_query(fkey)
        if new_rel:
            orig_rel.__sql_query.insert(1, 'join {} on'.format(__sql_id(rel)))
            orig_rel.__sql_query.insert(2, rel.__sql_query)
        if orig_rel != rel:
            orig_rel.__sql_values = (rel.__sql_values + orig_rel.__sql_values)

def __select_args(self, *args, **kwargs):
    """Returns the what, where and values needed to construct the queries.
    """
    def __set_ops(self, where, set_fields, set_ops_tree):
        print("{}\n{}\n{}\n".format(80*'.', set_ops_tree, 80*'.'))
        self_op = set_ops_tree.op_[0][0]
        where.append(" {} ".format(self_op))
        for op_, left, right in set_ops_tree:
            l_where = []
            if id(left) == id(self):
                coucou
                pass # do something
            else:
                l_set_fields = left.__get_set_fields()
                set_fields += l_set_fields
                for field in l_set_fields:
                    comp_str = '%s'
                    if type(field.value) in [list, tuple]:
                        comp_str = 'any(%s)'
                    l_where.append(
                        "{} {} {}".format(
                            praf(field.name()), field.comp(), comp_str))
                l_where = " and ".join(l_where)

            o_where = []
            o_set_fields = right.__get_set_fields()
            set_fields += o_set_fields
            for field in o_set_fields:
                comp_str = '%s'
                if type(field.value) in [list, tuple]:
                    comp_str = 'any(%s)'
                o_where.append(
                    "{} {} %s".format(
                        praf(field.name()), field.comp(), comp_str))
            o_where = " and ".join(o_where)
            o_where = "(({}) {} ({}))".format(l_where, op_, o_where)
            where.append(o_where)

    for fieldname, value in kwargs.items():
        self.__setattr__(fieldname, value)
    id_ = 'r{}'.format(id(self))
    def praf(field_name):
        """Returns field_name prefixed with relation alias."""
        if self.__query == 'select':
            return '{}.{}'.format(id_, field_name)
        return field_name
    what = '*'
    if args:
        what = ', '.join([praf(field_name) for field_name in args])
    set_fields = self.__get_set_fields()
    where = []
    for field in set_fields:
        comp_str = '%s'
        if type(field.value) is list:
            comp_str = 'any(%s)'
        where.append("{} {} {}".format(
            praf(field.name()), field.comp(), comp_str))
    if where:
        where = '{}'.format(" and ".join(where))
        if self.__set_ops_tree.neg:
            where = "not({})".format(where)
        where = [where]
    if self.__set_ops_tree.is_set():
        __set_ops(self, where, set_fields, self.__set_ops_tree)
    if where:
        where = 'where {}'.format("".join(where))
    else:
        where = ''
    return what, where, set_fields

def __get_query(self, query_template, *args, **kwargs):
    """Prepare the SQL query to be executed."""
    self.__sql_values = []
    self.__query = 'select'
    what, where, values = self.__select_args(*args, **kwargs)
    if args:
        what = 'distinct {}'.format(what)
    self.__get_from()
    return (
        query_template.format(what, ' '.join(self.__sql_query), where), values)

def select(self, *args, **kwargs):
    """Generator. Yiels the result of the query as a dictionary.

    - @args are fields names to restrict the returned attributes
    - @kwargs: key is a field_name, value the constraint associated
      to that field
    """
    if kwargs and self.is_set():
        msg = """
        You can't use kwargs in select/mogrify if self is already set!
        {}\n{}""".format(self, kwargs)
        raise RuntimeError(msg)
    kk = set(kwargs.keys())
    try:
        assert kk.intersection(self._fields_names) == kk
    except:
        raise UnknownAttributeError(str(kk.difference(self._fields_names)))
    self.__sql_values = []
    query_template = "select {} from {} {}"
    query, values = self.__get_query(query_template, *args, **kwargs)
    values = tuple(self.__sql_values + values)
    try:
        if not self.__mogrify:
            self.__cursor.execute(query, values)
        else:
            yield self.__cursor.mogrify(query, values).decode('utf-8')
            return
    except Exception as err:
        sys.stderr.write(
            self.__cursor.mogrify(query, values).decode('utf-8'))
        raise err
    for elt in self.__cursor.fetchall():
        yield elt

def mogrify(self, *args, **kwargs):
    """Prints the select query."""
    self.__mogrify = True
    for elt in self.select(*args, **kwargs):
        print(elt)
    self.__mogrify = False

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
        vars = tuple(self.__sql_values + values)
        self.__cursor.execute(query, vars)
    except Exception as err:
        print(query, vars)
        raise err
    return self.__cursor.fetchone()['count']

def __update_args(self, **kwargs):
    """Returns the what, where an values for the update query."""
    what_fields = []
    new_values = []
    self.__query = 'update'
    _, where, values = self.__select_args()
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
    assert self.is_set() or no_clause

    query_template = "update {} set {} {}"
    what, where, values = self.__update_args(**kwargs)
    query = query_template.format(self.__fqrn, what, where)
    self.__cursor.execute(query, tuple(values))

def __what_to_insert(self):
    """Returns the field names and values to be inserted."""
    fields_names = []
    set_fields = self.__get_set_fields()
    if set_fields:
        fields_names = [field.name() for field in set_fields]
    return ", ".join(fields_names), set_fields

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
    _ = {self.__setattr__(field_name, value)
         for field_name, value in kwargs.items()}
    assert self.is_set() or no_clause
    query_template = "delete from {} {}"
    self.__query = 'delete'
    _, where, values = self.__select_args(**kwargs)
    query = query_template.format(self.__fqrn, where)
    self.__cursor.execute(query, tuple(values))

def __getitem__(self, key):
    raise NotImplementedError
    return self.__cursor.fetchall()[key]

@property
def set_ops_tree(self):
    """Return the set operations on self."""
    return self.__set_ops_tree

def __copy(self):
    return copy(self)

def __and__(self, other):
    new = self.__copy()
    new.__set_ops_tree.add(new, "and", other)
    return new
def __iand__(self, other):
    return self & other

def __or__(self, other):
    new = self.__copy()
    new.__set_ops_tree.add(new, "or", other)
    return new
def __ior__(self, other):
    return self | other

def __sub__(self, other):
    new = self.__copy()
    new.__set_ops_tree.add(new, "and not", other)
    return new
def __isub__(self, other):
    return self - other

def __neg__(self):
    new = self.__copy()
    print("NEG", id(new), id(self))
    new.__set_ops_tree.neg = not new.__set_ops_tree.neg
    print("NEG", id(new.__set_ops_tree.neg), id(self.__set_ops_tree.neg))
    return new

def __xor__(self, other):
    return (self | other) - (self & other)
def __ixor__(self, other):
    return self ^ other

#### END of Relation methods definition

COMMON_INTERFACE = {
    '__init__': __init__,
    '__call__': __call__,
    '__getitem__': __getitem__,
    '__get_set_fields': __get_set_fields,
    '__repr__': __repr__,
    'group_by': group_by,
    'to_json': to_json,
    'fields': fields,
    '__get_from': __get_from,
    '__get_query': __get_query,
    'fqrn': fqrn,
    'is_set': is_set,
    '__select_args': __select_args,
    'select': select,
    'mogrify': mogrify,
    '__len__': __len__,
    'get': get,
    'getone': getone,
    'set_ops_tree': set_ops_tree,
    '__copy': __copy,
    '__and__': __and__,
    '__iand__': __iand__,
    '__or__': __or__,
    '__ior__': __ior__,
    '__sub__': __sub__,
    '__isub__': __isub__,
    '__xor__': __xor__,
    '__ixor__': __ixor__,
    '__neg__': __neg__,
    '__join_query': __join_query,
    'insert': insert,
    '__what_to_insert': __what_to_insert,
    'update': update,
    '__update_args': __update_args,
    'delete': delete,
    'Transaction': Transaction,
    # test
    'set_ops': set_ops,
}

TABLE_INTERFACE = COMMON_INTERFACE
VIEW_INTERFACE = COMMON_INTERFACE
MVIEW_INTERFACE = COMMON_INTERFACE
FDATA_INTERFACE = COMMON_INTERFACE

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
        rel_class_names = {
            'r': 'Table',
            'v': 'View',
            'm': 'Materialized view',
            'f': 'Foreign data'}
        kind = metadata['tablekind']
        tbl_attr['__kind'] = rel_class_names[kind]
        rel_interfaces = {
            'r': TABLE_INTERFACE,
            'v': VIEW_INTERFACE,
            'm': MVIEW_INTERFACE,
            'f': FDATA_INTERFACE}
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
        ta_['_fields'] = set()
        ta_['__fkeys'] = set()
        ta_['_fields_names'] = set()
        dbm = ta_['model'].metadata
        flds = list(dbm['byname'][ta_['__sfqrn']]['fields'].keys())
        for field_name, f_metadata in dbm['byname'][
                ta_['__sfqrn']]['fields'].items():
            ta_[field_name] = Field(field_name, f_metadata)
            ta_['_fields'].add(ta_[field_name])
            ta_['_fields_names'].add(field_name)
        for field_name, f_metadata in dbm['byname'][
                ta_['__sfqrn']]['fields'].items():
            fkeyname = f_metadata.get('fkeyname')
            if fkeyname and fkeyname.find('fk') == -1:
                fkeyname = '{}_fkey'.format(fkeyname)
                if ta_.get(fkeyname) and isinstance(ta_[fkeyname], Field):
                    fkeyname = '{}_fkey'.format(fkeyname)
            if fkeyname and not fkeyname in ta_:
                ft_ = dbm['byid'][f_metadata['fkeytableid']]
                ft_sfqrn = ft_['sfqrn']
                fields_names = [flds[elt-1]
                                for elt in f_metadata['keynum']]
                ft_fields_names = [ft_['fields'][elt]
                                   for elt in f_metadata['fkeynum']]
                ta_[fkeyname] = FKey(
                    fkeyname, ft_sfqrn, ft_fields_names, fields_names)
                ta_['__fkeys'].add(ta_[fkeyname])

def relation(_fqrn, **kwargs):
    """This function is used to instanciate a Relation object using
    its FQRN (Fully qualified relation name):
    <database name>.<schema name>.<relation name>.
    If the <schema name> comprises a dot it must be enclosed in double
    quotes. Dots are not allowed in <database name> and <relation name>.
    """
    return RelationFactory(None, None, {'fqrn': _fqrn})(**kwargs)

def _normalize_fqrn(_fqrn):
    """
    Transform <db name>.<schema name>.<table name> in
    "<db name>"."<schema name>"."<table name>".
    Dots are allowed only in the schema name.
    """
    _fqrn = _fqrn.replace('"', '')
    dbname, schema_table = _fqrn.split('.', 1)
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
