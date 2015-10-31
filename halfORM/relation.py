# pylint: disable=protected-access

"""This module provides: relation, RelationFactory

The relation function allows you to directly instanciate a Relation object
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
  name. Double quotes can be ommited even if there are dots in the schema name.

"""

__copyright__ = "Copyright (c) 2015 Joël Maïzi"
__license__ = """
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys
from halfORM import relation_errors
from halfORM.transaction import Transaction

#### THE following METHODS are included in Relation class according to
#### relation type (Table or View). See table_interface and view_interface.

def __init__(self, **kwargs):
    self.__cursor = self.model.connection.cursor()
    self.__cons_fields = []
    dct = self.__class__.__dict__
    [dct[field_name].set(value) for field_name, value in kwargs.items()]

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
        if hasattr(obj, 'timetuple'):
            # retruns # seconds since the epoch
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
    ret = []#[60 * '=']
    ret.append("{}: {}".format(rel_kind.upper(), self.__fqrn))
    if self.__metadata['description']:
        ret.append("DESCRIPTION:\n{}".format(self.__metadata['description']))
#    ret.append(('- cluster: {dbname}\n'
#                '- schema:  {schemaname}\n'
#                '- {__kind}:   {relationname}').format(**vars(self.__class__)))
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

def __get_set_fkeys(self):
    """Retruns a list containing only the foreign keys that are set."""
    return [fkey for fkey in self.__fkeys if fkey.is_set]

@property
def __from(self):
    """Returns FQRN aliased by r{id}."""
    join = ''
    values = []
    set_fkeys = self.__get_set_fkeys()
    if set_fkeys:
        for key in set_fkeys:
            join, values = key.join(self)
    return "{} as r{} {}".format(self.__fqrn, id(self), join), values

def __select_args(self, *args, **kwargs):
    """Returns the what, where and values needed to construct the queries.
    """
    id_ = 'r{}'.format(id(self))
    def praf(field_name):
        """Returns field_name prefixed with relation alias."""
        if kwargs['__query'] == 'select':
            return '{}.{}'.format(id_, field_name)
        return field_name
    dct = self.__class__.__dict__
    what = praf('*')
    if args:
        what = ', '.join([praf(dct[field_name].name) for field_name in args])
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

def select(self, *args, **kwargs):
    """Generator. Yiels the result of the query as a dictionary.

    - @args are fields names to restrict the returned attributes
    - @kwargs: limit, order by, distinct... options
    """
    query_template = "select {} from {} {}"
    what, where, values = self.__select_args(*args, __query='select', **kwargs)
    from_, join_values = self.__from
    query = query_template.format(what, from_, where)
    print(values, join_values)
    self.__cursor.execute(query, tuple(values + join_values))
    for elt in self.__cursor.fetchall():
        yield elt

def get(self, **kwargs):
    """Yields instanciated Relation objects instead of dict."""
    for dct in self.select(**kwargs):
        elt = self(**dct)
        yield elt

def getone(self, **kwargs):
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
    what, where, values = self.__select_args(*args, __query='select', **kwargs)
    from_, join_values = self.__from
    query = query_template.format(what, from_, where)
    self.__cursor.execute(query, tuple(values + join_values))
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
    fields_names = []
    values = ()
    set_fields = self.__get_set_fields()
    if set_fields:
        fields_names = [field.name for field in set_fields]
        values = [field.value for field in set_fields]
    return ", ".join(fields_names), values

def insert(self):
    query_template = "insert into {} ({}) values ({})"
    fields_names, values = self.__what_to_insert()
    what_to_insert = ", ".join(["%s" for i in range(len(values))])
    query = query_template.format(self.__fqrn, fields_names, what_to_insert)
    self.__cursor.execute(query, tuple(values))

def delete(self, no_clause=False, **kwargs):
    """
    kwargs is {[field name:value]}
    The object self must be set unless no_clause is false.
    """
    dct = self.__class__.__dict__
    [dct[field_name].set(value) for field_name, value in kwargs.items()]
    assert self.is_set or no_clause
    query_template = "delete from {} {}"
    _, where, values = self.__select_args(__query='delete')
    query = query_template.format(self.__fqrn, where)
    self.__cursor.execute(query, tuple(values))

def __iter__(self):
    raise NotImplementedError

def __getitem__(self, key):
    return self.__cursor.fetchall()[key]

def none(self, *args, **kwargs):
    """Returns None. Overwrites the __get_set_fkeys for views"""
    return None

transaction = Transaction

#### END of Relation methods definition

table_interface = {
    # shared with view_interface

    '__init__': __init__,
    '__call__': __call__,
    '__iter__': __iter__,
    '__getitem__': __getitem__,
    '__get_set_fields': __get_set_fields,
    '__get_set_fkeys': __get_set_fkeys,
    '__repr__': __repr__,
    'json': json,
    'fields': fields,
    '__from': __from,
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
    'transaction': transaction
}

view_interface = {
    '__init__': __init__,
    '__call__': __call__,
    '__iter__': __iter__,
    '__getitem__': __getitem__,
    '__get_set_fields': __get_set_fields,
    '__get_set_fkeys': none,
    '__repr__': __repr__,
    'json': json,
    'fields': fields,
    '__from': __from,
    'fqrn': fqrn,
    'is_set': is_set,
    '__select_args': __select_args,
    'select': select,
    '__len__': __len__,
    'get': get,
    'getone': getone,
}

class Relation():
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
        rel_interfaces = {'r': table_interface, 'v': view_interface}
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
        fields = list(dbm['byname'][ta_['__sfqrn']]['fields'].keys())
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
                fields_names = [fields[elt-1]
                                for elt in f_metadata['keynum']]
                ft_fields_names = [ft_['fields'][elt]
                                   for elt in f_metadata['fkeynum']]
                ta_[fkeyname] = FKey(
                    fkeyname, ft_sfqrn, ft_fields_names, fields_names)
                ta_['__fkeys'].append(ta_[fkeyname])

def relation(fqrn, **kwargs):
    """This function is used to instanciate a Relation object using
    its FQRN (Fully qualified relation name):
    <database name>.<schema name>.<relation name>.
    If the <schema name> comprises a dot it must be enclosed in double
    quotes. Dots are not allowed in <database name> and <relation name>.
    """
    return RelationFactory(None, None, {'fqrn': fqrn})(**kwargs)

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
