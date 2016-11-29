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
both FQRN and QRN. The _normalize_fqrn function add double quotes to the FQRN.
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
        super().__init__(
            "ERROR! Unknown attribute: {}.".format(msg))

class ExpectedOneElementError(Exception):
    """Expected one element error"""
    def __init__(self, msg):
        super().__init__(
            "ERROR! More than one element for a non list item: {}.".format(msg))

class SetOp(object):
    """SetOp class stores the set operations made on the Relation class objects

    - __op is one of {'or', 'and', 'sub', 'neg'}
    - __right is a Relation object. It can be None if the operator is 'neg'.
    """
    def __init__(self, left, op=None, right=None):
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

    def __repr__(self):
        return "{} {}".format(
            self.__op,
            self.__right and self.__right._fqrn or None)

class Relation(object):
    """Base class of Table and View classes (see relation_factory)."""
    pass

#### THE following METHODS are included in Relation class according to
#### relation type (Table or View). See TABLE_INTERFACE and VIEW_INTERFACE.

def __init__(self, **kwargs):
    """The arguments names must correspond to the columns names of the relation.
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
    self.__neg = False
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
    _ = {self._fields.__dict__[field_name].set(value)
         for field_name, value in kwargs.items()}
    self._joined_to = {}
    self.__query_type = None
    self.__sql_query = []
    self.__sql_values = []
    self.__mogrify = False
    self.__set_op = SetOp(self)
    self.__select_params = {}
    self.__id_cast = None
    _ = {field._set_relation(self) for field in self._fields.values()}
    _ = {fkey._set_relation(self) for fkey in self._fkeys.values()}
    if not self.__fkeys_properties:
        self._set_fkeys_properties()
        self.__fkeys_properties = True

@property
def id_(self):
    """Return the __id_cast or the id of the relation.
    """
    return self.__id_cast or id(self)

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
    for fkeyname, f_metadata in dbm['byname'][self.__sfqrn]['fkeys'].items():
        ft_sfqrn, ft_fields_names, fields_names = f_metadata
        pyfkeyname = iskeyword(fkeyname) and "{}_".format(fkeyname) or fkeyname
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
    """Retruns a dictionary containing only the values of the fields
    that are set."""
    return {key:field.value for key, field in
            self._fields.items() if field.is_set()}

def _to_dict_val_comp(self):
    """Retruns a dictionary containing the values and comparators of the fields
    that are set."""
    return {key:(field.value, field.comp()) for key, field in
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
    for _, jt_ in self._joined_to.items():
        joined_to |= jt_.is_set()
    return (joined_to or self.__set_op.op_ or self.__neg or
            bool({field for field in self._fields.values() if field.is_set()}))

def __get_set_fields(self):
    """Retruns a list containing only the fields that are set."""
    return [field for field in self._fields.values() if field.is_set()]

def __walk_op(self, rel_id_, out=None, _fields_=None):
    """Walk the set operators tree and return a list of SQL where
    representation of the query with a list of the fields of the query.
    """
    if out is None:
        out = []
        _fields_ = []
    if self.__set_op.op_:
        if self.__neg:
            out.append("not (")
        out.append("(")
        left = self.__set_op.left
        left.__query_type = self.__query_type
        left.__walk_op(rel_id_, out, _fields_)
        if self.__set_op.right is not None:
            out.append(" {}\n    ".format(self.__set_op.op_))
            right = self.__set_op.right
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
            #sys.stderr.write("déjà vu in from! {}\n".format(fk_rel._fqrn))
            continue
        deja_vu[fk_rel.id_].append((fk_rel, fkey))
        if fk_rel.__set_op.op_:
            fk_rel.__get_from(self.id_)
        _, where, values = fk_rel.__where_args()
        where = " and\n    {}".format(where)
        orig_rel.__sql_query.insert(1, '\n  join {} on\n   '.format(__sql_id(fk_rel)))
        orig_rel.__sql_query.insert(2, fkey._join_query(orig_rel))
        orig_rel.__sql_query.append(where)
        orig_rel.__sql_values += values

def __sql_id(self):
    """Returns the FQRN as alias for the sql query."""
    return "{} as r{}".format(self._fqrn, self.id_)

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
    ret = "({})".format(" and\n    ".join(where_repr) or "1 = 1")
    if self.__neg:
        ret = "not ({})".format(ret)
    return ret

def __where_args(self, *args):
    """Returns the what, where and values needed to construct the queries.
    """
    rel_id_ = self.id_
    what = 'r{}.*'.format(rel_id_)
    if args:
        what = ', '.join(['r{}.{}'.format(rel_id_, arg) for arg in args])
    s_where, set_fields = self.__walk_op(rel_id_)
    s_where = ''.join(s_where)
    if s_where == '()':
        s_where = '(1 = 1)'
    return what, s_where, set_fields

def __get_query(self, query_template, *args):
    """Prepare the SQL query to be executed."""
    self.__sql_values = []
    self.__query_type = 'select'
    what, where, values = self.__where_args(*args)
    where = "\nwhere\n    {}".format(where)
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
    query_template = "select\n  {}\nfrom\n  {}\n  {}"
    query, values = self.__get_query(query_template, *args)
    values = tuple(self.__sql_values + values)
    if 'limit' in self.__select_params.keys():
        query = '{} limit {}'.format(query, self.__select_params['limit'])
    if 'offset' in self.__select_params.keys():
        query = "{} offset {}".format(query, self.__select_params['offset'])
    if 'order_by' in self.__select_params.keys():
        query = "{} order by {}".format(
            query,
            ", ".join(["r{}.{}".format(self._id, field_name)
                       for field_name in self.__select_params['order_by']]))
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
    self.__query = "select"
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
    self.__query = "select"
    query_template = "select\n  distinct count({})\nfrom\n  {}\n  {}"
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
    self.__query_type = 'update'
    _, where, values = self.__where_args()
    where = " where {}".format(where)
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
        self._fields.__dict__[field_name].set(value)

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
    self.__query_type = 'insert'
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
    self.__query_type = 'delete'
    _, where, values = self.__where_args()
    where = " where {}".format(where)
    query = query_template.format(self._fqrn, where)
    self.__cursor.execute(query, tuple(values))

def __call__(self, **kwargs):
    return self.__class__(**kwargs)

def cast(self, qrn):
    """Cast a relation into another relation.
    """
    new = self._model._import_class(qrn)(**self._to_dict_val_comp())
    new.__id_cast = id(self)
    new._joined_to = self._joined_to
    new.__set_op = self.__set_op
    return new

def __set__op__(self, op_=None, right=None):
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
    if op_:
        new.__set_op.left = self
        new.__set_op.op_ = op_
    dct_join = self._joined_to
    if right is not None:
        new.__set_op.right = right
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
    new = self.__set__op__(self.__set_op.op_, self.__set_op.right)
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

def _set_fkeys_properties(self):
    """Property generator for fkeys.
    @args is a list of tuples (proerty_name, fkey_name)
    """
    fkp = __import__(self.__module__, globals(), locals(), ['FKEYS_PROPERTIES'], 0)
    if hasattr(fkp, 'FKEYS_PROPERTIES'):
        for property_name, fkey_name in fkp.FKEYS_PROPERTIES:
            self._set_fkey_property(property_name, fkey_name)

def _set_fkey_property(self, property_name, fkey_name):
    """Sets the property with property_name on the foreign key."""
    def fget(self):
        "getter"
        return self._fkeys.__dict__[fkey_name]()
    def fset(self, value):
        "setter"
        self._fkeys.__dict__[fkey_name].set(value)
    setattr(self.__class__, property_name, property(fget=fget, fset=fset))

def _debug():
    """For debug usage"""
    pass

#### END of Relation methods definition

COMMON_INTERFACE = {
    '__init__': __init__,
    'id_': id_,
    '__set_fields': __set_fields,
    'select_params': select_params,
    '__call__': __call__,
    'cast': cast,
    '__get_set_fields': __get_set_fields,
    '__repr__': __repr__,
    'group_by':group_by,
    'to_json': to_json,
    'to_dict': to_dict,
    '_to_dict_val_comp': _to_dict_val_comp,
    '__get_from': __get_from,
    '__get_query': __get_query,
    'is_set': is_set,
    '__where_repr': __where_repr,
    '__where_args': __where_args,
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

    bases = [Relation,]
    tbl_attr = {}
    tbl_attr['__fkeys_properties'] = False
    tbl_attr['_fqrn'], sfqrn = _normalize_fqrn(dct['fqrn'])
    tbl_attr['_qrn'] = tbl_attr['_fqrn'].split('.', 1)[1].replace('"', '')
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
    tbl_attr['_fkeys'] = []
    rel_interfaces = {
        'r': TABLE_INTERFACE,
        'v': VIEW_INTERFACE,
        'm': MVIEW_INTERFACE,
        'f': FDATA_INTERFACE}
    for fct_name, fct in rel_interfaces[kind].items():
        tbl_attr[fct_name] = fct
    class_name = _gen_class_name(rel_class_names[kind], sfqrn)
    rel_class = type(class_name, tuple(bases), tbl_attr)
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
