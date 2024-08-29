#-*- coding: utf-8 -*-
# pylint: disable=protected-access, too-few-public-methods, no-member

"""This module is used by the `model <#module-half_orm.model>`_ module
to generate the classes that manipulate the data in your database
with the `Model.get_relation_class <#half_orm.model.Model.get_relation_class>`_
method.


Example:
    >>> from half_orm.model import Model
    >>> model = Model('halftest')
    >>> class Person(model.get_relation_class('actor.person')):
    >>>     # your code goes here

Main methods provided by the class Relation:
- ho_insert: inserts a tuple into the pg table.
- ho_select: returns a generator of the elements of the set defined by
  the constraint on the Relation object. The elements are dictionaries with the
  keys corresponding to the selected columns names in the relation.
  The result is affected by the methods: ho_distinct, ho_order_by, ho_limit and ho_offset
  (see below).
- ho_update: updates the set defined by the constraint on the Relation object
  with the values passed as arguments.
- ho_delete: deletes from the relation the set of elements defined by the constraint
  on the Relation object.
- ho_get: returns the unique element defined by the constraint on the Relation object.
  the element returned if of the type of the Relation object.

The following methods can be chained on the object before a select.

- ho_distinct: ensures that there are no duplicates on the select result.
- ho_order_by: sets the order of the select result.
- ho_limit: limits the number of elements returned by the select method.
- ho_offset: sets the offset for the select method.

"""

import inspect
from functools import wraps
from collections import OrderedDict
from typing import List
import psycopg2
from psycopg2.extras import RealDictCursor

from half_orm import relation_errors
from half_orm.transaction import Transaction
from half_orm.field import Field
from half_orm import utils

class _SetOperators:
    """_SetOperators class stores the set operations made on the Relation class objects

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

class Relation:
    """Used as a base class for the classes generated by
    `Model.get_relation_class <#half_orm.model.Model.get_relation_class>`_.

    Args:
        **kwargs: the arguments names must correspond to the columns names of the relation.

    Raises:
        UnknownAttributeError: If the name of an argument doesn't match a column name in the
            relation considered.

    Examples:
        You can generate a class for any relation in your database:
            >>> from half_orm.model import Model
            >>> model = Model('halftest')
            >>> class Person(model.get_relation_class('actor.person')):
            >>>     # your code

        To define a set of data in your relation at instantiation:
            >>> gaston = Person(last_name='Lagaffe', first_name='Gaston')
            >>> all_names_starting_with_la = Person(last_name=('ilike', 'la%'))

        Or to constrain an instantiated object via its\
            `Fields <#half_orm.field.Field>`_:
            >>> person = Person()
            >>> person.birth_date = ('>', '1970-01-01')

        Raises an `UnknownAttributeError <#half_orm.relation_errors.UnknownAttributeError>`_:
            >>> Person(lost_name='Lagaffe')
            [...]UnknownAttributeError: ERROR! Unknown attribute: {'lost_name'}.
    """

    def __call__(self):
        "To indicate this class is indeed callable (Sonarcloud)"

#### THE following METHODS are included in Relation class according to
#### relation type (Table or View). See TABLE_INTERFACE and VIEW_INTERFACE.

def __init__(self, **kwargs):
    _fqrn = ""
    """The names of the arguments must correspond to the names of the columns in the relation.
    """
    module = __import__(self.__module__, globals(), locals(), ['FKEYS_PROPERTIES', 'FKEYS'], 0)
    #TODO: remove in release 1.0.0
    if hasattr(module, 'FKEYS_PROPERTIES') or hasattr(module, 'FKEYS'):
        mod_fkeys = utils.Color.bold(module.__name__ + '.FKEYS')
        err = f'''{mod_fkeys} variable is no longer supported!\n'''
        err += f'''\tUse the "{utils.Color.bold(self.__class__.__name__ + '.Fkeys')}"''' + \
            ''' class attribute instead.\n'''
        raise DeprecationWarning(err)
    self.__ho_fk_loop = set()
    self._ho_fields = {}
    self._ho_pkey = {}
    self._ho_fkeys = OrderedDict()
    self.__fkeys_attr = set()
    self._ho_join_to = {}
    self._ho_is_singleton = False
    self.__only = False
    self.__neg = False
    self.__set_fields()
    self.__set_fkeys()
    self.__query = ""
    self.__query_type = None
    self.__sql_query = []
    self.__sql_values = []
    self.__set_operators = _SetOperators(self)
    self.__select_params = {}
    self.__id_cast = None
    self.__cursor = self._model._connection.cursor(cursor_factory=RealDictCursor)
    self.__mogrify = False
    self.__check_columns(*kwargs.keys())
    _ = {self.__dict__[field_name].set(value)
         for field_name, value in kwargs.items() if value is not None}
    self.__isfrozen = True

def __check_columns(self, *args):
    "Check that the args are actual columns of the relation"
    columns = {elt.replace('"', '') for elt in args}
    if columns.intersection(self._ho_fields.keys()) != columns:
        diff = columns.difference(self._ho_fields.keys())
        raise relation_errors.UnknownAttributeError(', '.join([elt for elt in args if elt in diff]))

#@utils.trace
def ho_insert(self, *args) -> '[dict]':
    """Insert a new tuple into the Relation.

    Returns:
        [dict]: A singleton containing the data inserted.

    Example:
        >>> gaston = Person(last_name='La', first_name='Ga', birth_date='1970-01-01').ho_insert()
        >>> print(gaston)
        {'id': 1772, 'first_name': 'Ga', 'last_name': 'La', 'birth_date': datetime.date(1970, 1, 1)}

    Note:
        It is not possible to insert more than one row with the insert method
    """
    _ = args and args != ('*',) and self.__check_columns(*args)
    query_template = "insert into {} ({}) values ({})"
    self.__query_type = 'insert'
    fields_names, values, fk_fields, fk_query, fk_values = self.__what()
    what_to_insert = ["%s" for _ in range(len(values))]
    if fk_fields:
        fields_names += fk_fields
        what_to_insert += fk_query
        values += fk_values
    query = query_template.format(self._qrn, ", ".join(fields_names), ", ".join(what_to_insert))
    returning = args or ['*']
    if returning:
        query = self.__add_returning(query, *returning)
    self.__execute(query, tuple(values))
    res = [dict(elt) for elt in self.__cursor.fetchall()] or [{}]
    return res[0]

#@utils.trace
def ho_select(self, *args):
    """Gets the set of values correponding to the constraint attached to the object.
    This method is a generator.

    Arguments:
        *args: the fields names of the returned attributes. If omitted,
            all the fields are returned.

    Yields:
        the result of the query as a dictionary.

    Example:
        >>> for person in Person(last_name=('like', 'La%')).ho_select('id'):
        >>>     print(person)
        {'id': 1772}
    """
    self.__check_columns(*args)
    query, values = self._ho_prep_select(*args)
    self.__execute(query, values)
    for elt in self.__cursor:
        yield dict(elt)

#@utils.trace
def ho_get(self, *args: List[str]) -> Relation:
    """The get method allows you to fetch a singleton from the database.
    It garantees that the constraint references one and only one tuple.

    Args:
        args (List[str]): list of fields names.\
        If ommitted, all the values of the row retreived from the database\
        are set for the self object.\
        Otherwise, only the values listed in the `args` parameter are set.

    Returns:
        Relation: the object retreived from the database.

    Raises:
        ExpectedOneError: an exception is raised if no or more than one element is found.

    Example:
        >>> gaston = Person(last_name='Lagaffe', first_name='Gaston').ho_get()
        >>> type(gaston) is Person
        True
        >>> gaston.id
        (int4) NOT NULL (id = 1772)
        >>> str(gaston.id)
        '1772'
        >>> gaston.id.value
        1772
    """
    self.__check_columns(*args)
    self.ho_limit(2)
    _count = self.ho_count()
    if _count != 1:
        raise relation_errors.ExpectedOneError(self, _count)
    self._ho_is_singleton = True
    ret = self(**(next(self.ho_select(*args))))
    ret._ho_is_singleton = True
    return ret

#@utils.trace
def __fkey_where(self, where, values):
    _, _, fk_fields, fk_query, fk_values = self.__what()
    if fk_fields:
        fk_where = " and ".join([f"({a}) in ({b})" for a, b in zip(fk_fields, fk_query)])
        if fk_where:
            where = f"{where} and {fk_where}"
        values += fk_values
    return where, values

#@utils.trace
def ho_update(self, *args, update_all=False, **kwargs):
    """
    kwargs represents the values to be updated {[field name:value]}
    The object self must be set unless update_all is True.
    The constraints of self are updated with kwargs.
    """
    if not (self.ho_is_set() or update_all):
        raise RuntimeError(
            f'Attempt to update all rows of {self.__class__.__name__}'
            ' without update_all being set to True!')

    _ = args and args != ('*',) and self.__check_columns(*args)
    self.__check_columns(*(kwargs.keys()))
    update_args = dict(kwargs)
    for key, value in kwargs.items():
        # None values are first removed
        if value is None:
            update_args.pop(key)
    if not update_args:
        return None # no new value update. Should we raise an error here?

    query_template = "update {} set {} {}"
    what, where, values = self.__update_args(**update_args)
    where, values = self.__fkey_where(where, values)
    query = query_template.format(self._qrn, what, where)
    if args:
        query = self.__add_returning(query, *args)
    self.__execute(query, tuple(values))
    for field_name, value in update_args.items():
        self._ho_fields[field_name].set(value)
    if args:
        return [dict(elt) for elt in self.__cursor.fetchall()]
    return None

#@utils.trace
def ho_delete(self, *args, delete_all=False):
    """Removes a set of tuples from the relation.
    To empty the relation, delete_all must be set to True.
    """
    _ = args and args != ('*',) and self.__check_columns(*args)
    if not (self.ho_is_set() or delete_all):
        raise RuntimeError(
            f'Attempt to delete all rows from {self.__class__.__name__}'
            ' without delete_all being set to True!')
    query_template = "delete from {} {}"
    _, values = self.__prep_query(query_template)
    self.__query_type = 'delete'
    _, where, _ = self.__where_args()
    where, values = self.__fkey_where(where, values)
    if where:
        where = f" where {where}"
    query = f"delete from {self._qrn} {where}"
    if args:
        query = self.__add_returning(query, *args)
    self.__execute(query, tuple(values))
    if args:
        return [dict(elt) for elt in self.__cursor.fetchall()]
    return None

@staticmethod
def __add_returning(query, *args) -> str:
    "Adds the SQL returning clause to the query"
    if args:
        returning = ', '.join(args)
        return f'{query} returning {returning}'
    return query

def ho_unfreeze(self):
    "Allow to add attributs to a relation"
    self.__isfrozen = False

def ho_freeze(self):
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

#@utils.trace
def __execute(self, query, values):
    try:
        if self.__mogrify:
            print(self.__cursor.mogrify(query, values).decode('utf-8'))
        return self.__cursor.execute(query, values)
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        self._model.ping()
        self.__cursor = self._model._connection.cursor(cursor_factory=RealDictCursor)
        return self.__cursor.execute(query, values)

@property
def ho_id(self):
    """Return the __id_cast or the id of the relation.
    """
    return self.__id_cast or id(self)

@property
def ho_only(self):
    "Returns the value of self.__only"
    return self.__only
@ho_only.setter
def ho_only(self, value):
    """Set the value of self.__only. Restrict the values of a query to
    the elements of the relation (no inherited values).
    """
    if value not in {True, False}:
        raise ValueError(f'{value} is not a bool!')
    self.__only = value

def __set_fields(self):
    """Initialise the fields of the relation."""
    _fields_metadata = self._model._fields_metadata(self._t_fqrn)

    for field_name, f_metadata in _fields_metadata.items():
        field = Field(field_name, self, f_metadata)
        self._ho_fields[field_name] = field
        setattr(self, field_name, field)
        if field._is_part_of_pk():
            self._ho_pkey[field_name] = field

def __set_fkeys(self):
    """Initialisation of the foreign keys of the relation"""
    #pylint: disable=import-outside-toplevel
    from half_orm.fkey import FKey

    _fkeys_metadata = self._model._fkeys_metadata(self._t_fqrn)
    for fkeyname, f_metadata in _fkeys_metadata.items():
        self._ho_fkeys[fkeyname] = FKey(fkeyname, self, *f_metadata)
    if hasattr(self.__class__, 'Fkeys') and not self.__fkeys_properties:
        for key, value in self.Fkeys.items():
            try:
                if key != '': # we skip empty keys
                    setattr(self, key, self._ho_fkeys[value])
                    self.__fkeys_attr.add(key)
            except KeyError as exp:
                raise relation_errors.WrongFkeyError(self, value) from exp
    self.__fkeys_properties = True

def ho_dict(self):
    """Returns a dictionary containing only the values of the fields
    that are set."""
    return {key:field.value for key, field in self._ho_fields.items() if field.is_set()}

def __to_dict_val_comp(self):
    """Returns a dictionary containing the values and comparators of the fields
    that are set."""
    return {key:(field._comp(), field.value) for key, field in
            self._ho_fields.items() if field.is_set()}

def __repr__(self):

    fkeys_usage = """\
To use the foreign keys as direct attributes of the class, copy/paste the Fkeys below into
your code as a class attribute and replace the empty string key(s) with the alias(es) you
want to use. The aliases must be unique and different from any of the column names. Empty
string keys are ignored.

Fkeys = {"""

    rel_kind = self.__kind
    ret = []
    database, schema, relation = self._t_fqrn
    ret.append(f"DATABASE: {database}")
    ret.append(f"SCHEMA: {schema}")
    ret.append(f"{rel_kind.upper()}: {relation}\n")
    if self.__metadata['description']:
        ret.append(f"DESCRIPTION:\n{self.__metadata['description']}")
    ret.append('FIELDS:')
    mx_fld_n_len = 0
    for field_name in self._ho_fields.keys():
        mx_fld_n_len = max(mx_fld_n_len, len(field_name))
    for field_name, field in self._ho_fields.items():
        ret.append(f"- {field_name}:{' ' * (mx_fld_n_len + 1 - len(field_name))}{repr(field)}")
    ret.append('')
    pkey = self._model._pkey_constraint(self._t_fqrn)
    if pkey:
        ret.append(f"PRIMARY KEY ({', '.join(pkey)})")
    for uniq in self._model._unique_constraints_list(self._t_fqrn):
        ret.append(f"UNIQUE CONSTRAINT ({', '.join(uniq)})")
    if self._ho_fkeys.keys():
        plur = 'S' if len(self._ho_fkeys) > 1 else ''
        ret.append(f'FOREIGN KEY{plur}:')
        for fkey in self._ho_fkeys.values():
            ret.append(repr(fkey))
        ret.append('')
        ret.append(fkeys_usage)
        for fkey in self._ho_fkeys:
            ret.append(f"    '': '{fkey}',")
        ret.append('}')
    return '\n'.join(ret)

def ho_is_set(self):
    """Return True if one field at least is set or if self has been
    constrained by at least one of its foreign keys or self is the
    result of a combination of Relations (using set operators).
    """
    joined_to = False
    for _, jt_ in self._ho_join_to.items():
        jt_id = id(jt_)
        if jt_id in self.__ho_fk_loop:
            raise RuntimeError("Can't set Fkey on the same object")
        self.__ho_fk_loop.add(jt_id)
        joined_to |= jt_.ho_is_set()
    self.__ho_fk_loop = set()
    return (joined_to or bool(self.__set_operators.operator) or bool(self.__neg) or
            bool({field for field in self._ho_fields.values() if field.is_set()}))

def __get_set_fields(self):
    """Returns a list containing only the fields that are set."""
    return [field for field in self._ho_fields.values() if field.is_set()]

#@utils.trace
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

def __sql_id(self):
    """Returns the FQRN as alias for the sql query."""
    return f"{self._qrn} as r{self.ho_id}"

#@utils.trace
def __get_from(self, orig_rel=None, deja_vu=None):
    """Constructs the __sql_query and gets the __sql_values for self."""
    if deja_vu is None:
        orig_rel = self
        self.__sql_query = [__sql_id(self)]
        deja_vu = {self.ho_id:[(self, None)]}
    for fkey, fk_rel in self._ho_join_to.items():
        fk_rel.__query_type = orig_rel.__query_type
        if fk_rel.ho_id not in deja_vu:
            deja_vu[fk_rel.ho_id] = []
        # elif (fk_rel, fkey) in deja_vu[fk_rel.ho_id] or fk_rel is orig_rel:
        #     #sys.stderr.write(f"déjà vu in from! {fk_rel._fqrn}\n")
        #     continue
        fk_rel.__get_from(orig_rel, deja_vu)
        deja_vu[fk_rel.ho_id].append((fk_rel, fkey))
        _, where, values = fk_rel.__where_args()
        where = f" and\n {where}"
        orig_rel.__sql_query.insert(1, f'\n  join {__sql_id(fk_rel)} on\n   ')
        orig_rel.__sql_query.insert(2, fkey._join_query(self))
        orig_rel.__sql_query.append(where)
        orig_rel.__sql_values += values

#@utils.trace
def __where_repr(self, rel_id_):
    where_repr = []
    for field in self.__get_set_fields():
        where_repr.append(field._where_repr(self.__query_type, rel_id_))
    where_repr = ' and '.join(where_repr) or '1 = 1'
    ret = f"({where_repr})"
    if self.__neg:
        ret = f"not ({ret})"
    return ret

#@utils.trace
def __where_args(self, *args):
    """Returns the what, where and values needed to construct the queries.
    """
    rel_id_ = self.ho_id
    what = f'r{rel_id_}.*'
    if args:
        what = ', '.join([f'r{rel_id_}.{arg}' for arg in args])
    s_where, set_fields = self.__walk_op(rel_id_)
    s_where = ''.join(s_where)
    return what, s_where, set_fields

#@utils.trace
def __prep_query(self, query_template, *args):
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
    for fkey_name in self.__fkeys_attr:
        fkey_cls = self.__dict__[fkey_name].__class__
        if fkey_cls != FKey:
            raise RuntimeError(
                f'self.{fkey_name} is not a FKey (got a {fkey_cls.__name__} object instead).\n'
                f'- use: self.{fkey_name}.set({fkey_cls.__name__}(...))\n'
                f'- not: self.{fkey_name} = {fkey_cls.__name__}(...)'
                )
    # print('XXX __prep_query', what, self.__sql_query, where, values)
    return (
        query_template.format(
            what,
            self.__only and "only" or "",
            ' '.join(self.__sql_query), where),
        values)

#@utils.trace
def _ho_prep_select(self, *args):
    distinct = self.__select_params.get('distinct', '')
    query_template = f"select\n {distinct} {{}}\nfrom\n  {{}} {{}}\n  {{}}"
    query, values = self.__prep_query(query_template, *args)
    values = tuple(self.__sql_values + values)
    if 'order_by' in self.__select_params:
        query = f"{query} order by {self.__select_params['order_by']}"
    if 'limit' in self.__select_params:
        query = f"{query} limit {self.__select_params['limit']}"
    if 'offset' in self.__select_params:
        query = f"{query} offset {self.__select_params['offset']}"
    return query, values

def ho_distinct(self):
    """Set distinct in SQL select request."""
    self.__select_params['distinct'] = 'distinct'
    return self

def ho_unaccent(self, *fields_names):
    "Sets unaccent for each field listed in fields_names"
    for field_name in fields_names:
        if not isinstance(self.__dict__[field_name], Field):
            raise ValueError(f'{field_name} is not a Field!')
        self.__dict__[field_name].unaccent = True
    return self

def ho_order_by(self, _order_):
    """Set SQL order by according to the "order" string passed

    @order string example :
    "field1, field2 desc, field3, field4 desc"
    """
    self.__select_params['order_by'] = _order_
    return self

def ho_limit(self, _limit_):
    """Set limit for the next SQL select request."""
    if _limit_:
        self.__select_params['limit'] = int(_limit_)
    elif 'limit' in self.__select_params:
        self.__select_params.pop('limit')
    return self

def ho_offset(self, _offset_):
    """Set the offset for the next SQL select request."""
    self.__select_params['offset'] = int(_offset_)
    return self

def ho_mogrify(self):
    """Prints the select query."""
    self.__mogrify = True
    return self

# @utils.trace
def ho_count(self):
    """Returns the number of tuples matching the intention in the relation.

    See select for arguments.
    """
    self.__query = "select"
    query_template = "select\n  count(distinct {})\nfrom {}\n  {}\n  {}"
    query, values = self.__prep_query(query_template)
    vars_ = tuple(self.__sql_values + values)
    self.__execute(query, vars_)
    return self.__cursor.fetchone()['count']

def __len__(self):
    utils.deprectated('the usage of len', 'the Relation.ho_count method', '0.13.0', r'\s*list\(')
    return self.ho_count()

def ho_is_empty(self):
    """Returns True if the relation is empty, False otherwise.

    Same as __len__ but limits the request to 1 element (faster).
    Use it instead of len(relation) == 0.
    """
    self.__query = "select"
    query_template = "select\n  count(distinct {})\nfrom {}\n  {}\n  {} limit 1"
    query, values = self.__prep_query(query_template)
    vars_ = tuple(self.__sql_values + values)
    self.__execute(query, vars_)
    return self.__cursor.fetchone()['count'] == 0

#@utils.trace
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

#@utils.trace
def __what(self):
    """Returns the constrained fields and foreign keys.
    """
    set_fields = self.__get_set_fields()
    fields_names = [
        f'"{name}"' for name, field in self._ho_fields.items() if field.is_set()]
    fk_fields = []
    fk_queries = ''
    fk_values = []
    for fkey in self._ho_fkeys.values():
        fk_prep_select = fkey._fkey_prep_select()
        if fk_prep_select is not None:
            fk_values += list(fkey.values()[0])
            fk_fields += fk_prep_select[0]
            fk_queries = ["%s" for _ in range(len(fk_values))]

    return fields_names, set_fields, fk_fields, fk_queries, fk_values

@classmethod
def ho_description(self):
    """Returns the description (comment) of the relation
    """
    description = self.__metadata['description']
    if description:
        description = description.strip()
    return description or 'No description available'

def __call__(self, **kwargs):
    return self.__class__(**kwargs)

def ho_cast(self, qrn):
    """Cast a relation into another relation.

    TODO: check that qrn inherits self (or is inherited by self)?
    """
    new = self._model._import_class(qrn)(**self.__to_dict_val_comp())
    new.__id_cast = id(self)
    new._ho_join_to = self._ho_join_to
    new.__set_operators = self.__set_operators
    return new

def __set__op__(self, operator=None, right=None):
    """Si l'opérateur du self est déjà défini, il faut aller modifier
    l'opérateur du right ???
    On crée un nouvel objet sans contrainte et on a left et right et opérateur
    """
    def check_fk(new, jt_list):
        """Sets the _ho_join_to dictionary for the new relation.
        """
        for fkey, rel in jt_list.items():
            if rel is self:
                rel = new
            new._ho_join_to[fkey] = rel
    new = self(**self.__to_dict_val_comp())
    new.__id_cast = self.__id_cast
    if operator:
        new.__set_operators.left = self
        new.__set_operators.operator = operator
    dct_join = self._ho_join_to
    if right is not None:
        new.__set_operators.right = right
        dct_join.update(right._ho_join_to)
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
    return (right - self).ho_count() == 0

def __eq__(self, right):
    if id(self) == id(right):
        return True
    return self in right and right in self

def __enter__(self):
    """Context management entry

    Returns self in a transaction context.

    Example usage:
    with relation as rel:
        rel.ho_update(col=new_val)

    Equivalent to (in a transaction context):
    rel = relation.ho_select()
    for elt in rel:
        new_elt = relation(**elt)
        new_elt.ho_update(col=new_val)
    """
    self.ho_transaction._enter(self._model)
    return self

def __exit__(self, *__):
    """Context management exit

    """
    self.ho_transaction._exit(self._model)
    return False

def __iter__(self):
    query, values = self._ho_prep_select()
    self.__execute(query, values)
    liste = []
    for elt in self.__cursor:
        yield dict(elt)

def __next__(self):
    return next(self.ho_select())

def singleton(fct):
    """Decorator. Enforces the relation to define a singleton.

    _ho_is_singleton is set by Relation.get.
    _ho_is_singleton is unset as soon as a Field is set.
    """
    @wraps(fct)
    def wrapper(self, *args, **kwargs):
        if self._ho_is_singleton:
            return fct(self, *args, **kwargs)
        try:
            self = self.ho_get()
            return fct(self, *args, **kwargs)
        except relation_errors.ExpectedOneError as err:
            raise relation_errors.NotASingletonError(err)
    wrapper.__is_singleton = True
    wrapper.__orig_args = inspect.getfullargspec(fct)
    return wrapper

#### Deprecated

#### END of Relation methods definition

COMMON_INTERFACE = {
    '__init__': __init__,
    '__setattr__': __setattr__,
    '__execute': __execute,
    '__check_columns': __check_columns,
    '__set_fields': __set_fields,
    '__set_fkeys': __set_fkeys,
    '__call__': __call__,
    '__get_set_fields': __get_set_fields,
    '__repr__': __repr__,
    '__get_from': __get_from,
    '__prep_query': __prep_query,
    '__fkey_where': __fkey_where,
    '__where_repr': __where_repr,
    '__where_args': __where_args,
    'ho_count': ho_count,
    '__len__': __len__,

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
    '__what': __what,
    '__update_args': __update_args,
    '__add_returning': __add_returning,
    '__to_dict_val_comp': __to_dict_val_comp,
    '__enter__': __enter__,
    '__exit__': __exit__,
    '__iter__': __iter__,
    '__next__': __next__,

    # protected methods
    'ho_freeze': ho_freeze,
    'ho_unfreeze': ho_unfreeze,
    '_ho_prep_select': _ho_prep_select,
    'ho_mogrify': ho_mogrify,

    # public methods
    'ho_description': ho_description,
    'ho_id': ho_id,
    'ho_order_by': ho_order_by,
    'ho_limit': ho_limit,
    'ho_offset': ho_offset,
    'ho_distinct': ho_distinct,
    'ho_unaccent': ho_unaccent,
    'ho_cast': ho_cast,
    'ho_only': ho_only,
    'ho_is_empty': ho_is_empty,
    'ho_dict': ho_dict,
    'ho_is_set': ho_is_set,
    'ho_get': ho_get,
    'ho_insert': ho_insert,
    'ho_select': ho_select,
    'ho_update': ho_update,
    'ho_delete': ho_delete,

    'ho_transaction': Transaction,
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
