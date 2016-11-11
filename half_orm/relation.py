#-*- coding: utf-8 -*-
# pylint: disable=protected-access, too-few-public-methods, no-member

"""This module provides: relation, relation_factory

The relation function allows you to directly instanciate a Relation object
given its fully qualified relation name:
- relation(<FQRN>)

The relation_factory can be used to create classes to manipulate the relations
of the database:
```
class MyClass(metaclass=relation_factory):
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

from keyword import iskeyword
import datetime
import sys
import uuid
import yaml

from half_orm import relation_errors
from half_orm.transaction import Transaction

class UnknownAttributeError(Exception):
    """Unknown attribute error"""
    def __init__(self, msg):
        super(self.__class__, self).__init__(
            "ERROR! Unknown attribute: {}.".format(msg))

class ExpectedOneElementError(Exception):
    """Expected one element error"""
    def __init__(self, msg):
        super(self.__class__, self).__init__(
            "ERROR! More than one element for a non list item: {}.".format(msg))

class SetOp(object):
    """SetOp class stores the set operations made on the Relation class objects

    - __op is one of {'or', 'and', 'sub', 'neg'}
    - __right is a Relation object. It can be None if the operator is 'neg'.
    """
    def __init__(self, left, op=None, right=None):
        self.__neg = False
        self.__left = left
        self.__op = op
        self.__right = right

    def __get_op(self):
        """Property returning the __op value."""
        return self.__op
    def __set_op(self, op_):
        """Set operator setter."""
        self.__op = op_
    op_ = property(__get_op, __set_op)

    def __get_left(self):
        """Returns the left object of the set operation."""
        return self.__left
    def __set_left(self, left):
        """left operand (relation) setter."""
        self.__left = left
    left = property(__get_left, __set_left)

    def __get_right(self):
        """Property returning the right operand (relation)."""
        return self.__right
    def __set_right(self, right):
        """right operand (relation) setter."""
        self.__right = right
    right = property(__get_right, __set_right)

    def __get_neg(self):
        """returns the value of self.__neg."""
        return self.__neg
    def __set_neg(self, neg):
        """sets the value of self.__neg. The neg argument is not used."""
        self.__neg = neg
    neg = property(__get_neg, __set_neg)

    def __repr__(self):
        return "{}{} {}".format(
            self.__neg and "NOT " or "",
            self.__op,
            self.__right._fqrn)

class Relation(object):
    """Base class of Table and View classes (see relation_factory)."""
    _is_half_orm_relation = True


#### THE following METHODS are included in Relation class according to
#### relation type (Table or View). See TABLE_INTERFACE and VIEW_INTERFACE.

def __init__(self, **kwargs):
    """The arguments name must correspond to the attributes of the relation.
    """
    class FKeys(object):
        """Class of the Relation._fkeys attribute.
        Each foreign key of the PostgreSQL relation is accessible as an attribute
        of Relation._fkeys with the foreign key's name.
        """
        def __init__(self):
            self._fkeys_names = []

        def values(self):
            """Yields the foreign keys (FKey objects)"""
            for fkey_name in self._fkeys_names:
                yield self.__dict__[fkey_name]

        def __len__(self):
            return len(self.__dict__)

    class Fields(object):
        """Class of the Relation._fields attribute.
        Each attribute of the PostgreSQL relation is accessible as an attribute
        of Relation._fields with the field's name.
        """
        def __init__(self):
            self._fields_names = []

        def items(self):
            """Yields the (fields names, Field objects)"""
            for field_name in self._fields_names:
                yield field_name, self.__dict__[field_name]

        def keys(self):
            """Yields the fields names."""
            for field_name in self._fields_names:
                yield field_name

        def values(self):
            """Yields the fields (Field objects)"""
            for field_name in self._fields_names:
                yield self.__dict__[field_name]

        def __len__(self):
            return len(self.__dict__)
    self._fields = Fields()
    self._fkeys = FKeys()
    self._fields_names = set()
    self.__set_fields()
    self.__cursor = self._model._connection.cursor()
    self.__cons_fields = []
    kwk_ = set(kwargs.keys())
    try:
        assert kwk_.intersection(self._fields_names) == kwk_
    except:
        raise UnknownAttributeError(str(kwk_.difference(self._fields_names)))
    _ = {self._fields.__dict__[field_name]._set_value(value)
         for field_name, value in kwargs.items()}
    self._joined_to = []
    self.__query = None
    self.__sql_query = []
    self.__sql_values = []
    self.__mogrify = False
    self.__set_op = SetOp(self)
    self.__select_params = {}
    _ = {field._set_relation(self) for field in self._fields.values()}
    _ = {fkey._set_relation(self) for fkey in self._fkeys.values()}

def __set_fields(self):
    """Initialise the fields and fkeys of the relation."""
    from .field import Field
    from .fkey import FKey
    dbm = self._model._metadata
    flds = list(dbm['byname'][self.__sfqrn]['fields'].keys())
    for field_name, f_metadata in dbm['byname'][self.__sfqrn]['fields'].items():
        pyfield_name = (
            iskeyword(field_name) and "{}_".format(field_name) or field_name)
        self._fields._fields_names.append(pyfield_name)
        setattr(self._fields, pyfield_name, Field(field_name, f_metadata))
        self._fields_names.add(pyfield_name)
    for field_name, f_metadata in dbm['byname'][self.__sfqrn]['fields'].items():
        fkeyname = f_metadata.get('fkeyname')
        if fkeyname:
            pyfkeyname = (
                iskeyword(fkeyname) and "{}_".format(fkeyname) or fkeyname)
        if fkeyname and not hasattr(self._fkeys, pyfkeyname):
            ft_ = dbm['byid'][f_metadata['fkeytableid']]
            ft_sfqrn = ft_['sfqrn']
            fields_names = [flds[elt-1]
                            for elt in f_metadata['keynum']]
            ft_fields_names = [ft_['fields'][elt]
                               for elt in f_metadata['fkeynum']]
            self._fkeys._fkeys_names.append(pyfkeyname)
            setattr(
                self._fkeys,
                pyfkeyname,
                FKey(fkeyname, ft_sfqrn, ft_fields_names, fields_names))

def select_params(self, **kwargs):
    """Sets the limit and offset on the relation (used by select)."""
    self.__select_params.update(kwargs)
    return self

def group_by(self, yml_directive):
    """Returns an aggregation of the data according to the yml directive
    description.
    """
    def inner_group_by(data, directive, grouped_data, gdata=None):
        """reccursive fonction to actually group the data in grouped_data."""
        deja_vu_key = set()
        if gdata is None:
            gdata = grouped_data
        if isinstance(directive, list):
            directive = directive[0]
        keys = set(directive)
        for elt in data:
            res_elt = {}
            for key in keys.intersection(self._fields_names):
                deja_vu_key.add(directive[key])
                try:
                    res_elt.update({directive[key]:elt[key]})
                except:
                    raise UnknownAttributeError(key)
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
                    keys.intersection(self._fields_names)):
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
                    #TODO: Raise ExpectedOneElementError if necessary
                    gdata[group_name] = type_directive()
                    suite = gdata[group_name]
                else:
                    suite = gdata[group_name]
                inner_group_by(
                    [elt], directive[group_name], suite, None)

    grouped_data = {}
    data = [elt for elt in self.select()]
    directive = yaml.safe_load(yml_directive)
    inner_group_by(data, directive, grouped_data)
    return grouped_data

def to_json(self, yml_directive=None):
    """Returns a JSON representation of the set returned by the select query.
    """
    import json

    def handler(obj):
        """Replacement of default handler for json.dumps."""
        if hasattr(obj, 'isoformat'):
            return str(obj.isoformat())
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        elif isinstance(obj, datetime.timedelta):
            return obj.total_seconds()
        else:
            raise TypeError(
                'Object of type {} with value of '
                '{} is not JSON serializable'.format(type(obj), repr(obj)))

    if yml_directive:
        res = self.group_by(yml_directive)
    else:
        res = [elt for elt in self.select()]
    return json.dumps(res, default=handler)

def to_dict(self):
    """Retruns a dictionary containing only the fields that are set."""
    return {key:field.value for key, field in
            self._fields.items() if field.is_set()}

def __repr__(self):
    rel_kind = self.__kind
    ret = []
    if self._model._scope:
        ret.append("CLASS: {}".format(self.__class__))
        ret.append("DATABASE:")
        ret.append("- NAME: {}".format(self._model._dbinfo['name']))
        ret.append("- USER: {}".format(self._model._dbinfo['user']))
        ret.append("- HOST: {}".format(self._model._dbinfo['host']))
        ret.append("- PORT: {}".format(self._model._dbinfo['port']))
    else:
        ret.append("__RCLS: {}".format(self.__class__))
        ret.append(
            "This class allows you to manipulate the data in the PG relation:")
    ret.append("{}: {}".format(rel_kind.upper(), self._fqrn))
    if self.__metadata['description']:
        ret.append("DESCRIPTION:\n{}".format(self.__metadata['description']))
    ret.append('FIELDS:')
    mx_fld_n_len = 0
    for field_name in self._fields.keys():
        if len(field_name) > mx_fld_n_len:
            mx_fld_n_len = len(field_name)
    for field_name, field in self._fields.items():
        ret.append('- {}:{}{}'.format(
            field_name,
            ' ' * (mx_fld_n_len + 1 - len(field_name)),
            repr(field)))
    if self._fkeys._fkeys_names:
        plur = len(self._fkeys._fkeys_names) > 1 and  'S' or ''
        ret.append('FOREIGN KEY{}:'.format(plur))
        for fkey in self._fkeys.values():
            ret.append(repr(fkey))
    return '\n'.join(ret)

def is_set(self):
    """Return True if one field at least is set or if self has been
    constrained by at least one of its foreign keys or self is the
    result of a combination of Relations (using set operators).
    """
    joined_to = False
    for jt_, elt in self._joined_to:
        joined_to |= jt_.is_set()
    return (joined_to or
            (self.__set_op.op_ or self.__set_op.neg) or
            bool({field for field in self._fields.values() if field.is_set()}))

def __get_set_fields(self):
    """Retruns a list containing only the fields that are set."""
    return [field for field in self._fields.values() if field.is_set()]

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
                   for name in fkey._fields)
    to_fields = ('{}.{}'.format(to_id, name) for name in fkey.fk_names)
    bounds = op_.join(['{} = {}'.format(a, b) for
                       a, b in zip(to_fields, from_fields)])
    constraints_to_query = [
        field.where_repr('select', id(to_))
        for field in to_._fields.values() if field.is_set()]
    constraints_to_values = (
        field for field in to_._fields.values() if field.is_set())
    constraints_from_query = [
        field.where_repr('select', id(from_))
        for field in from_._fields.values() if field.is_set()]
    constraints_from_values = (
        field for field in from_._fields.values() if field.is_set())
    constraints_query = op_.join(
        constraints_to_query + constraints_from_query)
    constraints_values = list(constraints_to_values) + \
                         list(constraints_from_values)

    if constraints_query:
        bounds = op_.join([bounds, constraints_query])
    return str(bounds), constraints_values

def __get_from(self, orig_rel=None, deja_vu=None):
    """Constructs the __sql_query and gets the __sql_values for self."""
    def __sql_id(rel):
        """Returns the FQRN as alias for the sql query."""
        return "{} as r{}".format(rel._fqrn, id(rel))

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
            #sys.stderr.write("déjà vu in from! {}\n".format(rel._fqrn))
            continue
        deja_vu[id_rel].append((rel, fkey))
        rel.__get_from(orig_rel, deja_vu)
        rel.__sql_query, rel.__sql_values = rel.__join_query(fkey)
        if new_rel:
            orig_rel.__sql_query.insert(1, 'join {} on'.format(__sql_id(rel)))
            orig_rel.__sql_query.insert(2, rel.__sql_query)
        if id(orig_rel) != id(rel):
            orig_rel.__sql_values = (rel.__sql_values + orig_rel.__sql_values)

def __where_repr(self, query, id_):
    where_repr = []
    for field in self.__get_set_fields():
        where_repr.append(field.where_repr(query, id_))
    return "({})".format(" and ".join(where_repr))

def __select_args(self, *args):
    """Returns the what, where and values needed to construct the queries.
    """
    query = self.__query
    id_ = id(self)
    what = 'r{}.*'.format(id_)
    if args:
        what = ', '.join([self._fields.__dict__[arg]._praf(id_, query)
                          for arg in args])
    def walk_op(rel, out=None, _fields_=None):
        """Walk the set operators tree and return a list of SQL where
        representation of the query with a list of the fields of the query.
        """
        if rel is None:
            return out, _fields_
        if out is None:
            out = []
            _fields_ = []
        if rel.__set_op.op_ or rel.__set_op.neg:
            if rel.__set_op.neg:
                out.append("not")
            out.append("(")
            walk_op(rel.__set_op.left, out, _fields_)
            if rel.__set_op.op_ is not None:
                out.append(" {} ".format(rel.__set_op.op_))
                walk_op(rel.__set_op.right, out, _fields_)
            out.append(")")
        else:
            out.append(rel.__where_repr(query, id_))
            _fields_ += rel.__get_set_fields()
        return out, _fields_
    s_where, set_fields = walk_op(self)
    s_where = ''.join(s_where)
    if s_where == '()':
        s_where = ''
    if s_where:
        s_where = ' where {}'.format(s_where)
    return what, s_where, set_fields

def __get_query(self, query_template, *args):
    """Prepare the SQL query to be executed."""
    self.__sql_values = []
    self.__query = 'select'
    what, where, values = self.__select_args(*args)
    if args:
        what = 'distinct {}'.format(what)
    self.__get_from()
    return (
        query_template.format(what, ' '.join(self.__sql_query), where), values)

def select(self, *args):
    """Generator. Yiels the result of the query as a dictionary.

    - @args are fields names to restrict the returned attributes
    """
    self.__sql_values = []
    query_template = "select {} from {} {}"
    query, values = self.__get_query(query_template, *args)
    values = tuple(self.__sql_values + values)
    if 'limit' in self.__select_params.keys():
        query = '{} limit {}'.format(query, self.__select_params['limit'])
    if 'offset' in self.__select_params.keys():
        query = "{} offset {}".format(query, self.__select_params['offset'])
    try:
        if not self.__mogrify:
            self.__cursor.execute(query, values)
        else:
            yield self.__cursor.mogrify(query, values).decode('utf-8')
            return
    except Exception as err:
        sys.stderr.write(
            "QUERY: {}\nVALUES: {}\n".format(query, values))
        raise err
    for elt in self.__cursor.fetchall():
        yield elt

def _mogrify(self, *args):
    """Prints the select query."""
    self.__mogrify = True
    print([elt for elt in self.select(*args)][0])
    self.__mogrify = False

def get(self):
    """Returns the Relation object extracted.

    Raises an exception if no or more than one element is found.
    """
    count = len(self)
    if count != 1:
        raise relation_errors.ExpectedOneError(self, count)
    res = list(self.select())
    return self(**(res[0]))

def __len__(self, *args):
    """Retruns the number of tuples matching the intention in the relation.

    See select for arguments.
    """
    query_template = "select count({}) from {} {}"
    query, values = self.__get_query(query_template, *args)
    try:
        vars_ = tuple(self.__sql_values + values)
        self.__cursor.execute(query, vars_)
    except Exception as err:
        print(query, vars_)
        self._mogrify()
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

def update(self, update_all=False, **kwargs):
    """
    kwargs represents the values to be updated {[field name:value]}
    The object self must be set unless update_all is True.
    The constraints of the relations are updated with kwargs.
    """
    if not kwargs:
        return # no new value update. Should we raise an error here?
    assert self.is_set() or update_all

    query_template = "update {} set {} {}"
    what, where, values = self.__update_args(**kwargs)
    query = query_template.format(self._fqrn, what, where)
    self.__cursor.execute(query, tuple(values))
    for field_name, value in kwargs.items():
        self._fields.__dict__[field_name]._set_value(value)

def __what_to_insert(self):
    """Returns the field names and values to be inserted."""
    fields_names = []
    set_fields = self.__get_set_fields()
    if set_fields:
        fields_names = ['"{}"'.format(field.name()) for field in set_fields]
    return ", ".join(fields_names), set_fields

def insert(self):
    """Insert a new tuple into the Relation."""
    query_template = "insert into {} ({}) values ({})"
    fields_names, values = self.__what_to_insert()
    what_to_insert = ", ".join(["%s" for _ in range(len(values))])
    query = query_template.format(self._fqrn, fields_names, what_to_insert)
    self.__cursor.execute(query, tuple(values))

def delete(self, delete_all=False):
    """Removes a set of tuples from the relation.
    To empty the relation, delete_all must be set to True.
    """
    assert self.is_set() or delete_all
    query_template = "delete from {} {}"
    self.__query = 'delete'
    _, where, values = self.__select_args()
    query = query_template.format(self._fqrn, where)
    self.__cursor.execute(query, tuple(values))

def __call__(self, **kwargs):
    return self.__class__(**kwargs)

def dup(self):
    """Duplicate a Relation object"""
    new = relation_factory(None, None, {'fqrn': self._fqrn})(
        **{field.name():(field.value, field.comp())
           for field in self._fields.values() if field.value})
    new.__set_op.op_ = self.__set_op.op_
    if self.__set_op.right is not None:
        new.__set_op.right = self.__set_op.right.copy()
    return new

def __set__op__(self, op_, right):
    """Si l'opérateur du self est déjà défini, il faut aller modifier
    l'opérateur du right ???
    On crée un nouvel objet sans contrainte et on a left et right et opérateur
    """
    new = relation_factory(None, None, {'fqrn': self._fqrn})()
    new.__set_op.left = self
    new.__set_op.op_ = op_
    new.__set_op.right = right
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
    new = relation_factory(None, None, {'fqrn': self._fqrn})(
        **{field.name():(field.value, field.comp())
           for field in self._fields.values() if field.value})
    new.__set_op.neg = not self.__set_op.neg
    new.__set_op.left = self.__set_op.left
    new.__set_op.op_ = self.__set_op.op_
    new.__set_op.right = self.__set_op.right
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

def _debug():
    """For debug usage"""
    pass

#### END of Relation methods definition

COMMON_INTERFACE = {
    '__init__': __init__,
    '__set_fields': __set_fields,
    'select_params': select_params,
    '__call__': __call__,
    'dup': dup,
    '__get_set_fields': __get_set_fields,
    '__repr__': __repr__,
    'group_by':group_by,
    'to_json': to_json,
    'to_dict': to_dict,
    '__get_from': __get_from,
    '__get_query': __get_query,
    'is_set': is_set,
    '__where_repr': __where_repr,
    '__select_args': __select_args,
    'select': select,
    '_mogrify': _mogrify,
    '__len__': __len__,
    'get': get,
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
    '__join_query': __join_query,
    'insert': insert,
    '__what_to_insert': __what_to_insert,
    'update': update,
    '__update_args': __update_args,
    'delete': delete,
    'Transaction': Transaction,
    # test
    '_debug': _debug,
}

TABLE_INTERFACE = COMMON_INTERFACE
VIEW_INTERFACE = COMMON_INTERFACE
MVIEW_INTERFACE = COMMON_INTERFACE
FDATA_INTERFACE = COMMON_INTERFACE

def relation_factory(class_name, bases, dct):
    """Function to build a Relation class corresponding to a PostgreSQL
    relation.
    """
    from half_orm import model, model_errors
    def _gen_class_name(rel_kind, sfqrn):
        """Generates class name from relation kind and FQRN tuple"""
        class_name = "".join([elt.capitalize() for elt in
                              [elt.replace('.', '') for elt in sfqrn]])
        return "{}_{}".format(rel_kind, class_name)

    bases = (Relation,)
    tbl_attr = {}
    tbl_attr['_fqrn'], sfqrn = _normalize_fqrn(dct['fqrn'])
    attr_names = ['_dbname', '_schemaname', '_relationname']
    for i, name in enumerate(attr_names):
        tbl_attr[name] = sfqrn[i]
    dbname = tbl_attr['_dbname']
    tbl_attr['_model'] = model.Model._deja_vu(dbname)
    rel_class = model.Model._relations_['classes'].get(tuple(sfqrn))
    if rel_class:
        return rel_class
    if not tbl_attr['_model']:
        tbl_attr['_model'] = model.Model(dbname)
    try:
        metadata = tbl_attr['_model']._metadata['byname'][tuple(sfqrn)]
    except KeyError:
        raise model_errors.UnknownRelation(sfqrn)
    if metadata['inherits']:
        bases = []
    for parent_fqrn in metadata['inherits']:
        parent_fqrn = ".".join(['"{}"'.format(elt) for elt in parent_fqrn])
        bases.append(relation_factory(None, None, {'fqrn': parent_fqrn}))
    bases = tuple(bases)
    tbl_attr['__metadata'] = metadata
    if dct.get('model'):
        tbl_attr['_model'] = dct['model']
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
    for fct_name, fct in rel_interfaces[kind].items():
        tbl_attr[fct_name] = fct
    class_name = _gen_class_name(rel_class_names[kind], sfqrn)
    rel_class = type(class_name, bases, tbl_attr)
    tbl_attr['_model']._relations_['classes'][tuple(sfqrn)] = rel_class
    return rel_class

def relation(_fqrn, **kwargs):
    """This function is used to instanciate a Relation object using
    its FQRN (Fully qualified relation name):
    <database name>.<schema name>.<relation name>.
    If the <schema name> comprises a dot it must be enclosed in double
    quotes. Dots are not allowed in <database name> and <relation name>.
    """
    return relation_factory(None, None, {'fqrn': _fqrn})(**kwargs)

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
