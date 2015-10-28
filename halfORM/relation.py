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

"""

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
  Only the schema name can have dots in it. In this case, it must be written
  <database name>."<schema name>".<table name>
- QRN is the Qualified Relation Name. Same as the FQRN without the database
  name. Double quotes can be ommited even if there are dots in the schema name.

"""

import sys
from halfORM import relation_errors

#### THE following METHODS are included in Relation class according to
#### relation type (Table or View). See table_interface and view_interface.

def __init__(self, **kwargs):
    self.__cursor = self.model.connection.cursor()
    self.__cons_fields = []
    dct = self.__class__.__dict__
    [dct[field_name].set(value)for field_name, value in kwargs.items()]

def __call__(self, **kwargs):
    """__call__ method for the class Relation

    Instanciate a new object with all fields unset.
    """
    return relation(self.__fqrn, **kwargs)

def json(self):
    """TEST
    """
    import json, datetime, time
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
    return json.dumps([elt for elt in self.select()], default=handler)

def __repr__(self):
    rel_kind = self.__kind
    ret = [60*'-']
    ret.append("{}: {}".format(rel_kind, self.__fqrn))
    ret.append(('- cluster: {dbname}\n'
                '- schema:  {schemaname}\n'
                '- {__kind}:   {relationname}').format(**vars(self.__class__)))
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
    for fkey in self.__fkeys:
        ret.append(repr(fkey))
    return '\n'.join(ret)

def desc(self):
    return repr(self)

@property
def fqrn(self):
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
    for field in self.__fields:
        yield field

def __where(self):
    where = ''
    values = ()
    set_fields = [field for field in self.__fields if field.is_set]
    where_clause = ''
    if set_fields:
        where_clause = [
            '{} {} %s'.format(field.name, field.comp) for field in set_fields]
        where_clause = 'where {}'.format(" and ".join(where_clause))
        values = [field.value for field in set_fields]
    return where_clause, values

def select(self, *args, **kwargs):
    """Generator. Yiels result of query on dictionary form.

    - @args are fields names to restrict the returned attributes
    - @kwargs: limit, order by, distinct... options
    """
    dct = self.__class__.__dict__
    what = '*'
    if args:
        what = ', '.join([dct[field_name].name for field_name in args])
    where, values = self.__where()
    self.__cursor.execute(
        "select {} from {} {}".format(what, self.__fqrn, where), tuple(values))
    for elt in self.__cursor.fetchall():
        yield elt

def count(self, *args, **kwargs):
    """Better, still naive implementation of select

    - @args are fields names to restrict the returned attributes
    - @kwargs: limit, distinct, ...

    """
    dct = self.__class__.__dict__
    what = '*'
    if args:
        what = ', '.join([dct[field_name].name for field_name in args])
    where, values = self.__where()
    self.__cursor.execute(
        "select count({}) from {} {}".format(
            what, self.__fqrn, where), tuple(values))
    return self.__cursor.fetchone()['count']

def __update(self, **kwargs):
    what = []
    new_values = []
    for field_name, new_value in kwargs.items():
        what.append(field_name)
        new_values.append(new_value)
    return ", ".join(["{} = %s".format(elt) for elt in what]), new_values

def update(self, no_clause=False, **kwargs):
    """
    kwargs represents the values to be updated {[field name:value]}
    The object self must be set unless no_clause is false.
    """
    if not kwargs:
        return # no new value update. Should we raise an error here?
    assert self.is_set or no_clause
    where, values = self.__where()
    what, new_values = self.__update(**kwargs)
    query = "update {} set {} {}".format(self.__fqrn, what, where)
#    print(query, tuple(new_values + values))
    self.__cursor.execute(query, tuple(new_values + values))

def __what_to_insert(self):
    fields_names = []
    values = ()
    set_fields = [field for field in self.__fields if field.is_set]
    if set_fields:
        fields_names = [field.name for field in set_fields]
        values = [field.value for field in set_fields]
    return ", ".join(fields_names), values

def insert(self):
    fields_names, values = self.__what_to_insert()
    what_to_insert = ", ".join(["%s" for i in range(len(values))])
    self.__cursor.execute(
        "insert into {} ({}) values ({})".format(
            self.__fqrn, fields_names, what_to_insert),
        tuple(values))

def delete(self, no_clause=False, **kwargs):
    """
    kwargs is {[field name:value]}
    The object self must be set unless no_clause is false.
    """
    dct = self.__class__.__dict__
    [dct[field_name].set(value)for field_name, value in kwargs.items()]
    assert self.is_set or no_clause
    where, values = self.__where()
    self.__cursor.execute(
        "delete from {} {}".format(self.__fqrn, where), tuple(values))

def get(self, **kwargs):
    for dct in self.select(**kwargs):
        elt = self(**dct)
        yield elt

def getone(self, **kwargs):
    count = self.count()
    if count != 1:
        raise relation_errors.ExpectedOneError(self, count)
    return list(self.get())[0]

def __iter__(self):
    raise NotImplementedError

def __getitem__(self, key):
    return self.__cursor.fetchall()[key]

@staticmethod
def transaction(func):
    """func is a method of a Model object"""
    def wrapper(relation, *args, **kwargs):
        res = None
        try:
            relation.model.connection.autocommit = False
            res = func(relation, *args, **kwargs)
            relation.model.connection.commit()
            relation.model.connection.autocommit = True
        except Exception as err:
            sys.stderr.write(
                "Transaction error: {}\nRolling back!\n".format(err))
            relation.model.connection.rollback()
            relation.model.connection.autocommit = True
            raise err
        return res
    return wrapper

#### END of Relation methods definition

table_interface = {
    # shared with view_interface

    '__init__': __init__,
    '__call__': __call__,
    '__iter__': __iter__,
    '__getitem__': __getitem__,
    '__repr__': __repr__,
    'desc': desc,
    'json': json,
    'fields': fields,
    'fqrn': fqrn,
    'is_set': is_set,
    '__where': __where,
    'select': select,
    'count': count,
    'get': get,
    'getone': getone,

    # specific table

    'insert': insert,
    '__what_to_insert': __what_to_insert,
    'update': update,
    '__update': __update,
    'delete': delete,
    'transaction': transaction
}

view_interface = {
    '__init__': __init__,
    '__call__': __call__,
    '__iter__': __iter__,
    '__getitem__': __getitem__,
    '__repr__': __repr__,
    'desc': desc,
    'json': json,
    'fields': fields,
    'fqrn': fqrn,
    'is_set': is_set,
    '__where': __where,
    'select': select,
    'count': count,
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
        if dct.get('model'):
            tbl_attr['model'] = dct['model']
        tbl_attr['__sfqrn'] = tuple(sfqrn)
        attr_names = ['dbname', 'schemaname', 'relationname']
        for i in range(len(attr_names)):
            tbl_attr[attr_names[i]] = sfqrn[i]
        dbname = tbl_attr['dbname']
        tbl_attr['model'] = model.Model.deja_vu(dbname)
        if not tbl_attr['model']:
            tbl_attr['model'] = model.Model(dbname)
        rel_class_names = {'r': 'Table', 'v': 'View'}
        try:
            kind = (
                tbl_attr['model'].metadata['byname']
                [tuple(sfqrn)]['tablekind'])
            tbl_attr['__kind'] = rel_class_names[kind]
        except KeyError:
            raise model_errors.UnknownRelation(sfqrn)
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
        for field_name, metadata in dbm['byname'][
                ta_['__sfqrn']]['fields'].items():
            fkeyname = metadata.get('fkeyname')
            if fkeyname and not fkeyname in ta_:
                ft_ = dbm['byid'][metadata['fkeytableid']]
                ft_sfqrn = ft_['sfqrn']
                fields_names = [ft_['fields'][elt]
                                for elt in metadata['fkeynum']]
                ft_fields_names = [ft_['fields'][elt]
                                   for elt in metadata['fkeynum']]
                ta_[fkeyname] = FKey(
                    fkeyname, ft_sfqrn, ft_fields_names, fields_names)
                ta_['__fkeys'].append(ta_[fkeyname])
            ta_[field_name] = Field(field_name, metadata)
            ta_['__fields'].append(ta_[field_name])

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
