#-*- coding: utf-8 -*-
# pylint: disable=protected-access, too-few-public-methods, no-member

"""This module provides the class Relation.

This class is generated by model.get_relation_class.

Main methods provided by the class Relation:
- insert: inserts a tuple into the pg table.
- select: returns a generator of the elements of the set defined by
  the constraint on the Relation object. The elements are dictionaries with the
  keys corresponding to the selected columns names in the relation.
  The result is affected by the methods: distinct, order_by, limit and offset
  (see bellow).
- update: updates the set defined by the constraint on the Relation object
  with the values passed as arguments.
- delete: deletes from the relation the set of elements defined by the constraint
  on the Relation object.
- get: returns the unique element defined by the constraint on the Relation object.
  the element returned if of the type of the Relation object.
- count: returns the number of elements in the set defined by the constraint on the
  Relation object.

The following methods can be chained on the object before a select.

- distinct: ensures that there are no duplicates on the select result.
- order_by: sets the order of the select result.
- limit: limits the number of elements returned by the select method.
- offset: sets the offset for the select method.
"""

from functools import wraps
from collections import OrderedDict
from uuid import UUID
from typing import Generator
from datetime import date, datetime, time, timedelta
import json
import sys
import psycopg2


import yaml

from half_orm import relation_errors
from half_orm.transaction import Transaction
from half_orm.field import Field
from half_orm.pg_meta import normalize_fqrn, normalize_qrn

class SetOperators:
    """SetOperators class stores the set operations made on the Relation class objects

    - __operator is one of {'or', 'and', 'sub', 'neg'}
    - __right is a Relation object. It can be None if the operator is 'neg'.
    """
    def __init__(self, left, operator=None, right=None):
        self.__left = left
        self.__operator = operator
        self.__right = right

    @property
    def operator(self):
        """Property returning the __operator value."""
        return self.__operator
    @operator.setter
    def operator(self, operator):
        """Set operator setter."""
        self.__operator = operator

    @property
    def left(self):
        """Returns the left object of the set operation."""
        return self.__left
    @left.setter
    def left(self, left):
        """left operand (relation) setter."""
        self.__left = left

    @property
    def right(self):
        """Property returning the right operand (relation)."""
        return self.__right
    @right.setter
    def right(self, right):
        """right operand (relation) setter."""
        self.__right = right

    def __repr__(self):
        return f"{self.__operator} {self.__right and self.__right._fqrn or None}"

class Relation:
    """Base class of Table and View classes (see _factory)."""

#### THE following METHODS are included in Relation class according to
#### relation type (Table or View). See TABLE_INTERFACE and VIEW_INTERFACE.

def __init__(self, **kwargs):
    _fqrn = ""
    """The arguments names must correspond to the columns names of the relation.
    """
    self._fields = {}
    self._pkey = {}
    self._fkeys = OrderedDict()
    self._fkeys_prop = []
    self._fkeys_attr = set()
    self.__only = False
    self.__neg = False
    self.__set_fields()
    self.__set_fkeys()
    self._joined_to = {}
    self.__query = ""
    self.__query_type = None
    self.__sql_query = []
    self.__sql_values = []
    self.__set_operators = SetOperators(self)
    self.__select_params = {}
    self.__id_cast = None
    self.__cursor = self._model._connection.cursor()
    self.__cons_fields = []
    self.__mogrify = False
    self._is_singleton = False
    kwk_ = set(kwargs.keys())
    if kwk_.intersection(self._fields.keys()) != kwk_:
        raise relation_errors.UnknownAttributeError(str(kwk_.difference(self._fields.keys())))
    _ = {self.__dict__[field_name].set(value)
         for field_name, value in kwargs.items() if value is not None}
    self.__isfrozen = True

def _unfreeze(self):
    "Allow to add attributs to a relation"
    self.__isfrozen = False

def _freeze(self):
    "set __isfrozen to True."
    self.__isfrozen = True

def __setattr__(self, key, value):
    """Sets an attribute as long as __isfrozen is False

    The foreign keys properties are not detected by hasattr
    hence the line `_ = self.__dict__[key]` to double check if
    the attribute is really present.
    """
    if not hasattr(self, '__isfrozen'):
        object.__setattr__(self, '__isfrozen', False)
    if self.__isfrozen and not hasattr(self, key):
        raise relation_errors.IsFrozenError(self.__class__, key)
    if self.__dict__.get(key) and isinstance(self.__dict__[key], Field):
        self.__dict__[key].set(value)
        return
    object.__setattr__(self, key, value)

def __execute(self, query, values):
    try:
        if self.__mogrify:
            print(self.__cursor.mogrify(query, values).decode('utf-8'))
        return self.__cursor.execute(query, values)
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        self._model.ping()
        self.__cursor = self._model._connection.cursor()
        return self.__cursor.execute(query, values)

@property
def id_(self):
    """Return the __id_cast or the id of the relation.
    """
    return self.__id_cast or id(self)

@property
def only(self):
    "Returns the value of self.__only"
    return self.__only
@only.setter
def only(self, value):
    """Set the value of self.__only. Restrict the values of a query to
    the elements of the relation (no inherited values).
    """
    if not value in {True, False}:
        raise ValueError(f'{value} is not a bool!')
    self.__only = value

def __set_fields(self):
    """Initialise the fields of the relation."""
    fields_metadata = self._model.fields_metadata(self._t_fqrn)

    for field_name, f_metadata in fields_metadata.items():
        field = Field(field_name, self, f_metadata)
        self._fields[field_name] = field
        self.__setattr__(field_name, field)
        if field.is_pk():
            self._pkey[field_name] = field

def __set_fkeys(self):
    """Initialisation of the foreign keys of the relation"""
    #pylint: disable=import-outside-toplevel
    from half_orm.fkey import FKey

    fkeys_metadata = self._model.fkeys_metadata(self._t_fqrn)
    for fkeyname, f_metadata in fkeys_metadata.items():
        self._fkeys[fkeyname] = FKey(fkeyname, self, *f_metadata)
    if not self.__fkeys_properties:
        self._set_fkeys_properties()
        self.__fkeys_properties = True
    if hasattr(self, 'Fkeys'):
        for key, value in self.Fkeys.items():
            try:
                if key != '': # we skip empty keys
                    setattr(self.__class__.__base__, key, self._fkeys[value])
                    self._fkeys_attr.add(key)
            except KeyError as exp:
                raise relation_errors.WrongFkeyError(self, value) from exp

def _set_fkeys_properties(self):
    """Property generator for fkeys.
    @args is a list of tuples (property_name, fkey_name)
    """
    fkp = __import__(self.__module__, globals(), locals(), ['FKEYS_PROPERTIES', 'FKEYS'], 0)
    if hasattr(fkp, 'FKEYS_PROPERTIES'):
        sys.stderr.write(
            'WARNING! Depreciation:'
            f'Please replace FKEYS_PROPERTIES with FKEYS in {self.__class__}\n')
        for prop in fkp.FKEYS_PROPERTIES:
            self._set_fkey_property(*prop)
    if hasattr(fkp, 'FKEYS'):
        for prop in fkp.FKEYS:
            self._set_fkey_property(*prop)

def _set_fkey_property(self, property_name, fkey_name, _cast=None):
    """Sets the property with property_name on the foreign key."""
    if property_name == '':
        # Do nothing
        return
    def fget(self):
        "getter"
        return self._fkeys[fkey_name](__cast__=_cast)
    def fset(self, value):
        "setter"
        try:
            if value.is_set():
                self._fkeys[fkey_name].set(value)
        except KeyError as err:
            sys.stderr.write(
                f'ERR {err}\nFKeys for {self.__class__.__name__} are: {self._fkeys.keys()}\n')
            raise err
    if self.__dict__.get(property_name):
        raise relation_errors.DuplicateAttributeError(
            f"ERROR: Can't set '{property_name}' as a FKEY property in {self.__class__}!")
    self._fkeys_prop.append(property_name)
    setattr(self.__class__, property_name, property(fget=fget, fset=fset))

def group_by(self, yml_directive):
    """Returns an aggregation of the data according to the yml directive
    description.
    """
    def inner_group_by(data, directive, grouped_data, gdata=None):
        """recursive fonction to actually group the data in grouped_data."""
        deja_vu_key = set()
        if gdata is None:
            gdata = grouped_data
        if isinstance(directive, list):
            directive = directive[0]
        keys = set(directive)
        for elt in data:
            res_elt = {}
            for key in keys.intersection(self._fields.keys()):
                deja_vu_key.add(directive[key])
                try:
                    res_elt.update({directive[key]:elt[key]})
                except KeyError as exc:
                    raise relation_errors.UnknownAttributeError(key) from exc
            if isinstance(gdata, list):
                different = None
                for selt in gdata:
                    different = True
                    for key in deja_vu_key:
                        different = selt[key] != res_elt[key]
                        if different:
                            break
                    if not different:
                        break
                if not gdata or different:
                    gdata.append(res_elt)
            else:
                gdata.update(res_elt)
            for group_name in keys.difference(
                    keys.intersection(self._fields.keys())):
                type_directive = type(directive[group_name])
                suite = None
                if not gdata:
                    gdata[group_name] = type_directive()
                    suite = gdata[group_name]
                elif isinstance(gdata, list):
                    suite = None
                    for selt in gdata:
                        different = True
                        for skey in deja_vu_key:
                            different = selt[skey] != res_elt[skey]
                            if different:
                                break
                        if not different:
                            if selt.get(group_name) is None:
                                selt[group_name] = type_directive()
                            suite = selt[group_name]
                            break
                    if suite is None:
                        gdata.append(res_elt)
                elif gdata.get(group_name) is None:
                    #TODO: Raise ExpectedOneError if necessary
                    gdata[group_name] = type_directive()
                    suite = gdata[group_name]
                else:
                    suite = gdata[group_name]
                inner_group_by(
                    [elt], directive[group_name], suite, None)

    grouped_data = {}
    data = list(self.select())
    directive = yaml.safe_load(yml_directive)
    inner_group_by(data, directive, grouped_data)
    return grouped_data

def to_json(self, yml_directive=None, res_field_name='elements', **kwargs):
    """Returns a JSON representation of the set returned by the select query.
    if kwargs, returns {res_field_name: [list of elements]}.update(kwargs)
    """

    def handler(obj):
        """Replacement of default handler for json.dumps."""
        if hasattr(obj, 'isoformat'):
            return str(obj.isoformat())
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, timedelta):
            return obj.total_seconds()
        raise TypeError(
            f'Object of type {type(obj)} with value of {repr(obj)} is not JSON serializable')

    if yml_directive:
        res = self.group_by(yml_directive)
    else:
        res = [elt for elt in self.select()]
    if kwargs:
        res = {res_field_name: res}
        res.update(kwargs)
    return json.dumps(res, default=handler)

def to_dict(self):
    """Returns a dictionary containing only the values of the fields
    that are set."""
    return {key:field.value for key, field in self._fields.items() if field.is_set()}

def _to_dict_val_comp(self):
    """Returns a dictionary containing the values and comparators of the fields
    that are set."""
    return {key:(field.comp(), field.value) for key, field in
            self._fields.items() if field.is_set()}

def __repr__(self):

    fkeys_usage = """To use the foreign keys as direct attributes of the class, copy/paste the Fkeys bellow in
your code as a class attribute and replace the empty string(s) key(s) with the alias you
want to use. The aliases must be unique and different from any of the column names. Empty
string keys are ignored.

Fkeys = {"""

    rel_kind = self.__kind
    ret = []
    ret.append(f"__RCLS: {self.__class__}")
    ret.append(
        "This class allows you to manipulate the data in the PG relation:")
    ret.append(f"{rel_kind.upper()}: {self._fqrn}")
    if self.__metadata['description']:
        ret.append(f"DESCRIPTION:\n{self.__metadata['description']}")
    ret.append('FIELDS:')
    mx_fld_n_len = 0
    for field_name in self._fields.keys():
        if len(field_name) > mx_fld_n_len:
            mx_fld_n_len = len(field_name)
    for field_name, field in self._fields.items():
        ret.append(f"- {field_name}:{' ' * (mx_fld_n_len + 1 - len(field_name))}{repr(field)}")
    if self._fkeys.keys():
        plur = 'S' if len(self._fkeys) > 1 else ''
        ret.append(f'FOREIGN KEY{plur}:')
        for fkey in self._fkeys.values():
            ret.append(repr(fkey))
        ret.append('')
        ret.append(fkeys_usage)
        for fkey in self._fkeys:
            ret.append(f"    '': '{fkey}',")
        ret.append('}')
    return '\n'.join(ret)

def is_set(self):
    """Return True if one field at least is set or if self has been
    constrained by at least one of its foreign keys or self is the
    result of a combination of Relations (using set operators).
    """
    joined_to = False
    for _, jt_ in self._joined_to.items():
        joined_to |= jt_.is_set()
    return (joined_to or bool(self.__set_operators.operator) or bool(self.__neg) or
            bool({field for field in self._fields.values() if field.is_set()}))

def __get_set_fields(self):
    """Returns a list containing only the fields that are set."""
    return [field for field in self._fields.values() if field.is_set()]

def __walk_op(self, rel_id_, out=None, _fields_=None):
    """Walk the set operators tree and return a list of SQL where
    representation of the query with a list of the fields of the query.
    """
    if out is None:
        out = []
        _fields_ = []
    if self.__set_operators.operator:
        if self.__neg:
            out.append("not (")
        out.append("(")
        left = self.__set_operators.left
        left.__query_type = self.__query_type
        left.__walk_op(rel_id_, out, _fields_)
        if self.__set_operators.right is not None:
            out.append(f" {self.__set_operators.operator}\n    ")
            right = self.__set_operators.right
            right.__query_type = self.__query_type
            right.__walk_op(rel_id_, out, _fields_)
        out.append(")")
        if self.__neg:
            out.append(")")
    else:
        out.append(self.__where_repr(rel_id_))
        _fields_ += self.__get_set_fields()
    return out, _fields_

def __join(self, orig_rel, deja_vu):
    for fkey, fk_rel in self._joined_to.items():
        fk_rel.__query_type = orig_rel.__query_type
        fk_rel.__get_from(orig_rel, deja_vu)
        if fk_rel.id_ not in deja_vu:
            deja_vu[fk_rel.id_] = []
        elif (fk_rel, fkey) in deja_vu[fk_rel.id_] or fk_rel is orig_rel:
            #sys.stderr.write(f"déjà vu in from! {fk_rel._fqrn}\n")
            continue
        deja_vu[fk_rel.id_].append((fk_rel, fkey))
        if fk_rel.__set_operators.operator:
            fk_rel.__get_from(self.id_)
        _, where, values = fk_rel.__where_args()
        where = f" and\n    {where}"
        orig_rel.__sql_query.insert(1, f'\n  join {__sql_id(fk_rel)} on\n   ')
        orig_rel.__sql_query.insert(2, fkey._join_query(self))
        orig_rel.__sql_query.append(where)
        orig_rel.__sql_values += values

def __sql_id(self):
    """Returns the FQRN as alias for the sql query."""
    return f"{self._qrn} as r{self.id_}"

def __get_from(self, orig_rel=None, deja_vu=None):
    """Constructs the __sql_query and gets the __sql_values for self."""
    if deja_vu is None:
        orig_rel = self
        self.__sql_query = [__sql_id(self)]
        deja_vu = {self.id_:[(self, None)]}
    self.__join(orig_rel, deja_vu)

def __where_repr(self, rel_id_):
    where_repr = []
    for field in self.__get_set_fields():
        where_repr.append(field.where_repr(self.__query_type, rel_id_))
    where_repr = ' and\n    '.join(where_repr) or '1 = 1'
    ret = f"({where_repr})"
    if self.__neg:
        ret = f"not ({ret})"
    return ret

def __where_args(self, *args):
    """Returns the what, where and values needed to construct the queries.
    """
    rel_id_ = self.id_
    what = f'r{rel_id_}.*'
    if args:
        what = ', '.join([f'r{rel_id_}.{arg}' for arg in args])
    s_where, set_fields = self.__walk_op(rel_id_)
    s_where = ''.join(s_where)
    if s_where == '()':
        s_where = '(1 = 1)'
    return what, s_where, set_fields

def __get_query(self, query_template, *args):
    """Prepare the SQL query to be executed."""
    from half_orm.fkey import FKey

    self.__sql_values = []
    self.__query_type = 'select'
    what, where, values = self.__where_args(*args)
    where = f"\nwhere\n    {where}"
    self.__get_from()
    # remove duplicates
    for idx, elt in reversed(list(enumerate(self.__sql_query))):
        if elt.find('\n  join ') == 0 and self.__sql_query.count(elt) > 1:
            self.__sql_query[idx] = '  and\n'
    # check that fkeys are fkeys
    for fkey_name in self._fkeys_attr:
        fkey_cls = self.__class__.__base__.__dict__[fkey_name].__class__
        if fkey_cls != FKey:
            raise RuntimeError(
                f'self.{fkey_name} is not a FKey (got a {fkey_cls.__name__} object instead).\n'
                f'- use: self.{fkey_name}.set({fkey_cls.__name__}(...))\n'
                f'- not: self.{fkey_name} = {fkey_cls.__name__}(...)'
                )
    return (
        query_template.format(
            what,
            self.__only and "only" or "",
            ' '.join(self.__sql_query), where),
        values)

def _prep_select(self, *args):
    self.__sql_values = []
    query_template = f"select\n {self.__select_params.get('distinct', '')} {{}}\nfrom\n  {{}} {{}}\n  {{}}"
    query, values = self.__get_query(query_template, *args)
    values = tuple(self.__sql_values + values)
    if 'order_by' in self.__select_params.keys():
        query = f"{query} order by {self.__select_params['order_by']}"
    if 'limit' in self.__select_params.keys():
        query = f"{query} limit {self.__select_params['limit']}"
    if 'offset' in self.__select_params.keys():
        query = f"{query} offset {self.__select_params['offset']}"
    return query, values

def distinct(self):
    """Set distinct in SQL select request."""
    self.__select_params['distinct'] = 'distinct'
    return self

def unaccent(self, *fields_names):
    "Sets unaccent for each field listed in fields_names"
    for field_name in fields_names:
        if not isinstance(self.__dict__[field_name], Field):
            raise ValueError(f'{field_name} is not a Field!')
        self.__dict__[field_name].unaccent = True
    return self

def order_by(self, _order_):
    """Set SQL order by according to the "order" string passed

    @order string example :
    "field1, field2 desc, field3, field4 desc"
    """
    self.__select_params['order_by'] = _order_
    return self

def limit(self, _limit_):
    """Set limit for the next SQL select request."""
    self.__select_params['limit'] = _limit_
    return self

def offset(self, _offset_):
    """Set the offset for the next SQL select request."""
    self.__select_params['offset'] = _offset_
    return self

def select(self, *args) -> Generator[any, None, None]:
    """Generator. Yields the result of the query as a dictionary.

    - @args are fields names to restrict the returned attributes
    """
    query, values = self._prep_select(*args)
    try:
        self.__execute(query, values)
    except Exception as err:
        sys.stderr.write(f"QUERY: {query}\nVALUES: {values}\n")
        raise err
    return self.__cursor

def _mogrify(self):
    """Prints the select query."""
    self.__mogrify = True
    return self

def get(self):
    """Returns the Relation object extracted.

    Raises an exception if no or more than one element is found.
    """
    _count = len(self)
    if _count != 1:
        raise relation_errors.ExpectedOneError(self, _count)
    self._is_singleton = True
    ret = self(**(next(self.select())))
    ret._is_singleton = True
    return ret

def __len__(self):
    """Returns the number of tuples matching the intention in the relation.

    See select for arguments.
    """
    self.__query = "select"
    query_template = "select\n  count(distinct {})\nfrom {}\n  {}\n  {}"
    query, values = self.__get_query(query_template)
    try:
        vars_ = tuple(self.__sql_values + values)
        self.__execute(query, vars_)
    except Exception as err:
        self._mogrify()
        self.__execute(query, vars_)
        raise Exception from err
    return self.__cursor.fetchone()['count']

def is_empty(self):
    """Returns True if the relation is empty, False otherwise.

    Same as __len__ but limits the request to 1 element (faster).
    Use it instead of len(relation) == 0.
    """
    self.__query = "select"
    query_template = "select\n  count(distinct {})\nfrom {}\n  {}\n  {} limit 1"
    query, values = self.__get_query(query_template)
    try:
        vars_ = tuple(self.__sql_values + values)
        self.__execute(query, vars_)
    except Exception as err:
        print(query, vars_)
        raise err
    return self.__cursor.fetchone()['count'] != 1

def count(self, *args, _distinct=False):
    """Returns the number of tuples matching the intention in the relation.

    See select for arguments.
    """
    self.__query = "select"
    if _distinct:
        query_template = "select\n  count(distinct {})\nfrom {}\n  {}\n  {}"
    else:
        query_template = "select\n  count({})\nfrom {}\n  {}\n  {}"
    query, values = self.__get_query(query_template, *args)
    try:
        vars_ = tuple(self.__sql_values + values)
        self.__execute(query, vars_)
    except Exception as err:
        self._mogrify()
        self.__execute(query, vars_)
        raise Exception from err
    return self.__cursor.fetchone()['count']

def __update_args(self, **kwargs):
    """Returns the what, where an values for the update query."""
    what_fields = []
    new_values = []
    self.__query_type = 'update'
    _, where, values = self.__where_args()
    where = f" where {where}"
    for field_name, new_value in kwargs.items():
        what_fields.append(field_name)
        new_values.append(new_value)
    what = ", ".join([f'"{elt}" = %s' for elt in what_fields])
    return what, where, new_values + values

def update(self, update_all=False, **kwargs):
    """
    kwargs represents the values to be updated {[field name:value]}
    The object self must be set unless update_all is True.
    The constraints of the relations are updated with kwargs.
    """
    if not (self.is_set() or update_all):
        raise RuntimeError(
            f'Attempt to update all rows of {self.__class__.__name__}'
            ' without update_all being set to True!')

    update_args = dict(kwargs)
    for key, value in kwargs.items():
        # None values are first removed
        if value is None:
            update_args.pop(key)
    if not update_args:
        return # no new value update. Should we raise an error here?

    query_template = "update {} set {} {}"
    what, where, values = self.__update_args(**update_args)
    _, _, fk_fields, fk_query, fk_values = self.__what_to_insert()
    if fk_fields:
        fk_where = " and ".join([f"({a}) in ({b})" for a, b in zip(fk_fields, fk_query)])
        where = f"{where} and {fk_where}"
        values += fk_values
    query = query_template.format(self._qrn, what, where)
    self.__execute(query, tuple(values))
    for field_name, value in update_args.items():
        self._fields[field_name].set(value)

def __what_to_insert(self):
    """Returns the field names and values to be inserted."""
    fields_names = []
    set_fields = self.__get_set_fields()
    if set_fields:
        fields_names = [
            f'"{name}"' for name, field in self._fields.items() if field.is_set()]
    fk_fields = []
    fk_queries = ''
    fk_values = []
    for fkey in self._fkeys.values():
        fk_prep_select = fkey._prep_select()
        if fk_prep_select is not None:
            fk_values += list(fkey.values()[0])
            fk_fields += fk_prep_select[0]
            fk_queries = ["%s" for _ in range(len(fk_values))]

    return fields_names, set_fields, fk_fields, fk_queries, fk_values

def insert(self):
    """Insert a new tuple into the Relation."""
    query_template = "insert into {} ({}) values ({}) returning *"
    self.__query_type = 'insert'
    fields_names, values, fk_fields, fk_query, fk_values = self.__what_to_insert()
    what_to_insert = ["%s" for _ in range(len(values))]
    if fk_fields:
        fields_names += fk_fields
        what_to_insert += fk_query
        values += fk_values
    query = query_template.format(self._qrn, ", ".join(fields_names), ", ".join(what_to_insert))
    self.__execute(query, tuple(values))
    return self.__cursor.fetchall()

def delete(self, delete_all=False):
    """Removes a set of tuples from the relation.
    To empty the relation, delete_all must be set to True.
    """
    if not (self.is_set() or delete_all):
        raise RuntimeError(
            f'Attempt to delete all rows from {self.__class__.__name__}'
            ' without delete_all being set to True!')
    query_template = "delete from {} {}"
    _, values = self.__get_query(query_template)
    self.__query_type = 'delete'
    _, where, _ = self.__where_args()
    _, _, fk_fields, fk_query, fk_values = self.__what_to_insert()
    where = f" where {where}"
    if where == "(1 = 1)" and not delete_all:
        raise RuntimeError
    if fk_fields:
        fk_where = " and ".join([f"({a}) in ({b})" for a, b in zip(fk_fields, fk_query)])
        where = f"{where} and {fk_where}"
        values += fk_values
    query = query_template.format(self._qrn, where)
    self.__execute(query, tuple(values))

def __call__(self, **kwargs):
    return self.__class__(**kwargs)

def cast(self, qrn):
    """Cast a relation into another relation.
    """
    new = self._model._import_class(qrn)(**self._to_dict_val_comp())
    new.__id_cast = id(self)
    new._joined_to = self._joined_to
    new.__set_operators = self.__set_operators
    return new

def join(self, *f_rels):
    """Joins data to self.select() result. Returns a dict
    f_rels is a list of [(obj: Relation(), name: str, fields: Optional(<str|str[]>)), ...].

    Each obj in f_rels must have a direct or reverse fkey to self.
    If res is the result, res[name] contains the data associated to the element
    through the fkey or reversed fkey.
    If fields is a str, the data associated with res[name] is returned in a list (only one column).
    Otherwise (str[]), res[name] is a list of dict.
    If the fields argument is ommited, all the fields of obj are returned in a list of dict.

    Raises:
        RuntimeError: if self.__class__ and foreign.__class__ don't have fkeys to each other.

    Returns:
        dict: all values are converted to string.
    """
    from half_orm.fkey import FKey

    def to_str(value):
        """Returns value in string format if the type of value is
        in TO_PROCESS

        Args:
            value (any): the value to return in string format.
        """

        TO_PROCESS = {UUID, date, datetime, time, timedelta}
        if value.__class__ in TO_PROCESS:
            return str(value)
        return value

    res = list(
        {key: to_str(value) for key, value in elt.items()}
        for elt in self.distinct().select()
    )
    result_as_list = False
    ref = self()
    for f_rel in f_rels:
        if not isinstance(f_rel, tuple):
            raise RuntimeError("f_rels must be a list of tuples.")
        if len(f_rel) == 3:
            f_relation, name, fields = f_rel
        elif len(f_rel) == 2:
            f_relation, name = f_rel
            fields = list(f_relation._fields.keys())
        else:
            raise RuntimeError(f"f_rel must have 2 or 3 arguments. Got {len(f_rel)}.")
        if isinstance(fields, str):
            fields = [fields]
            result_as_list = True
        res_remote = {}

        f_relation_fk_names = []
        fkey_found = False
        for fkey_12 in ref._fkeys:
            if type(ref._fkeys[fkey_12]) != FKey:
                raise RuntimeError("This is not an Fkey")
            remote_fk = ref._fkeys[fkey_12]
            remote = remote_fk()
            if remote.__class__ == f_relation.__class__:
                for field in f_relation._fields.keys():
                    if f_relation.__dict__[field].is_set():
                        remote.__dict__[field].set(f_relation.__dict__[field])
                fkey_found = True
                f_relation_fk_names = remote_fk.fk_names
                break

        if not fkey_found:
            raise RuntimeError(f"No foreign key between {self._fqrn} and {f_relation._fqrn}!")
        inter = [{key: to_str(val) for key, val in elt.items()}
            for elt in remote.distinct().select(
                *([f'"{field}"' for field in fields] + f_relation_fk_names))]
        for elt in inter:
            key = tuple(elt[subelt] for subelt in f_relation_fk_names)
            if key not in res_remote:
                res_remote[key] = []
            if result_as_list:
                res_remote[key].append(to_str(elt[fields[0]]))
            else:
                res_remote[key].append({key: to_str(elt[key]) for key in fields})

        if f_relation_fk_names:
            d_res = {
                tuple(elt[selt] for selt in remote_fk.names): elt
                for elt in res
                }
            to_remove = set()
            for elt in d_res:
                remote = res_remote.get(elt)
                if remote:
                    d_res[elt][name] = remote
                else:
                    to_remove.add(elt)
            res = [elt for elt in res if tuple(elt[selt]
                    for selt in remote_fk.names) not in to_remove]
    return res

def __set__op__(self, operator=None, right=None):
    """Si l'opérateur du self est déjà défini, il faut aller modifier
    l'opérateur du right ???
    On crée un nouvel objet sans contrainte et on a left et right et opérateur
    """
    def check_fk(new, jt_list):
        """Sets the _joined_to dictionary for the new relation.
        """
        for fkey, rel in jt_list.items():
            if rel is self:
                rel = new
            new._joined_to[fkey] = rel
    new = self(**self._to_dict_val_comp())
    new.__id_cast = self.__id_cast
    if operator:
        new.__set_operators.left = self
        new.__set_operators.operator = operator
    dct_join = self._joined_to
    if right is not None:
        new.__set_operators.right = right
        dct_join.update(right._joined_to)
    check_fk(new, dct_join)
    return new

def __and__(self, right):
    return self.__set__op__("and", right)
def __iand__(self, right):
    self = self & right
    return self

def __or__(self, right):
    return self.__set__op__("or", right)
def __ior__(self, right):
    self = self | right
    return self

def __sub__(self, right):
    return self.__set__op__("and not", right)
def __isub__(self, right):
    self = self - right
    return self

def __neg__(self):
    new = self.__set__op__(self.__set_operators.operator, self.__set_operators.right)
    new.__neg = not self.__neg
    return new

def __xor__(self, right):
    return (self | right) - (self & right)
def __ixor__(self, right):
    self = self ^ right
    return self

def __contains__(self, right):
    return len(right - self) == 0

def __eq__(self, right):
    if id(self) == id(right):
        return True
    return self in right and right in self

def __ne__(self, right):
    return not self == right

def __enter__(self):
    """Context management entry

    Returns self in a transaction context.

    Example usage:
    with relation as rel:
        rel.update(col=new_val)

    Equivalent to (in a transaction context):
    rel = relation.select()
    for elt in rel:
        new_elt = relation(**elt)
        new_elt.update(col=new_val)
    """
    @self.Transaction
    def context(self):
        return self
    return context(self)

def __exit__(_, *__):
    """Context management exit

    Not much to do here.
    """
    return False

def singleton(fct):
    """Decorator. Enforces the relation to define a singleton.

    _is_singleton is set by Relation.get.
    _is_singleton is unset as soon as a Field is set.
    """
    @wraps(fct)
    def wrapper(self, *args, **kwargs):
        if self._is_singleton:
            return fct(self, *args, **kwargs)
        try:
            self = self.get()
            return fct(self, *args, **kwargs)
        except relation_errors.ExpectedOneError as err:
            raise relation_errors.NotASingletonError(err)
    return wrapper

def _debug(_):
    """For debug purpose"""

#### END of Relation methods definition

COMMON_INTERFACE = {
    '__init__': __init__,
    '_freeze': _freeze,
    '_unfreeze': _unfreeze,
    '__setattr__': __setattr__,
    '__execute': __execute,
    'id_': id_,
    '__set_fields': __set_fields,
    '__set_fkeys': __set_fkeys,
    'order_by': order_by,
    'limit': limit,
    'offset': offset,
    'distinct': distinct,
    'unaccent': unaccent,
    '__call__': __call__,
    'cast': cast,
    '__get_set_fields': __get_set_fields,
    '__repr__': __repr__,
    'only': only,
    'is_empty': is_empty,
    'group_by':group_by,
    'to_json': to_json,
    'to_dict': to_dict,
    '_to_dict_val_comp': _to_dict_val_comp,
    '__get_from': __get_from,
    '__get_query': __get_query,
    'is_set': is_set,
    '__where_repr': __where_repr,
    '__where_args': __where_args,
    '_prep_select': _prep_select,
    'select': select,
    '_mogrify': _mogrify,
    '__len__': __len__,
    'count': count,
    'get': get,
    'join': join,
    '__set__op__': __set__op__,
    '__and__': __and__,
    '__iand__': __iand__,
    '__or__': __or__,
    '__ior__': __ior__,
    '__sub__': __sub__,
    '__isub__': __isub__,
    '__xor__': __xor__,
    '__ixor__': __ixor__,
    '__neg__': __neg__,
    '__contains__': __contains__,
    '__eq__': __eq__,
    '__sql_id': __sql_id,
    '__walk_op': __walk_op,
    '__join': __join,
    'insert': insert,
    '__what_to_insert': __what_to_insert,
    'update': update,
    '__update_args': __update_args,
    'delete': delete,
    'Transaction': Transaction,
    '_set_fkeys_properties': _set_fkeys_properties,
    '_set_fkey_property': _set_fkey_property,
    '__enter__': __enter__,
    '__exit__': __exit__,
    # test
    '_debug': _debug,
    'singleton': singleton,
}


TABLE_INTERFACE = COMMON_INTERFACE
VIEW_INTERFACE = COMMON_INTERFACE
MVIEW_INTERFACE = COMMON_INTERFACE
FDATA_INTERFACE = COMMON_INTERFACE

REL_INTERFACES = {
    'r': TABLE_INTERFACE,
    'p': TABLE_INTERFACE,
    'v': VIEW_INTERFACE,
    'm': MVIEW_INTERFACE,
    'f': FDATA_INTERFACE}

REL_CLASS_NAMES = {
    'r': 'Table',
    'p': 'Partioned table',
    'v': 'View',
    'm': 'Materialized view',
    'f': 'Foreign data'}

def _factory(dct):
    """Function to build a Relation class corresponding to a PostgreSQL
    relation.
    """
    #pylint: disable=import-outside-toplevel
    from half_orm import model, model_errors
    def _gen_class_name(rel_kind, sfqrn):
        """Generates class name from relation kind and FQRN tuple"""
        class_name = "".join([elt.capitalize() for elt in
                              [elt.replace('.', '') for elt in sfqrn]])
        return f"{rel_kind}_{class_name}"

    bases = [Relation,]
    tbl_attr = {}
    tbl_attr['__base_classes'] = set()
    tbl_attr['__fkeys_properties'] = False
    tbl_attr['_qrn'] = normalize_qrn(dct['fqrn'])

    tbl_attr.update(dict(zip(['_dbname', '_schemaname', '_relationname'], dct['fqrn'])))
    if not tbl_attr['_dbname'] in model.Model._classes_:
        model.Model._classes_[tbl_attr['_dbname']] = {}
    if dct.get('model'):
        tbl_attr['_model'] = dct['model']
    else:
        tbl_attr['_model'] = model.Model._deja_vu(tbl_attr['_dbname'])
    rel_class = model.Model.check_deja_vu_class(*dct['fqrn'])
    if rel_class:
        return rel_class

    try:
        metadata = tbl_attr['_model'].relation_metadata(dct['fqrn'])
    except KeyError as exc:
        raise model_errors.UnknownRelation(dct['fqrn']) from exc
    if metadata['inherits']:
        metadata['inherits'].sort()
        bases = []
    for parent_fqrn in metadata['inherits']:
        bases.append(_factory({'fqrn': parent_fqrn}))
    tbl_attr['__metadata'] = metadata
    tbl_attr['_t_fqrn'] = dct['fqrn']
    tbl_attr['_fqrn'] = normalize_fqrn(dct['fqrn'])
    tbl_attr['__kind'] = REL_CLASS_NAMES[metadata['tablekind']]
    tbl_attr['_fkeys'] = []
    for fct_name, fct in REL_INTERFACES[metadata['tablekind']].items():
        tbl_attr[fct_name] = fct
    class_name = _gen_class_name(REL_CLASS_NAMES[metadata['tablekind']], dct['fqrn'])
    rel_class = type(class_name, tuple(bases), tbl_attr)
    model.Model._classes_[tbl_attr['_dbname']][dct['fqrn']] = rel_class
    return rel_class
