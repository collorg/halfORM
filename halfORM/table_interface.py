def __init__(self, **kwargs):
    self.__cursor = self.model.cursor()
    self.__cons_fields = []
    dct = self.__class__.__dict__
    [dct[field_name].set(value)for field_name, value in kwargs.items()]

def __repr__(self):
    tks = {'r': 'TABLE', 'v': 'VIEW'}
    table_kind = tks.get(self.__kind, "UNKNOWN TYPE")
    ret = [60*'-']
    ret.append("{}: {}".format(table_kind, self.fqtn))
    ret.append(('- cluster: {dbname}\n'
                '- schema:  {schemaname}\n'
                '- table:   {tablename}').format(**vars(self.__class__)))
    ret.append('FIELDS:')
    mx_fld_n_len = 0
    for field in self.__fields:
        if len(field.name) > mx_fld_n_len:
            mx_fld_n_len = len(field.name)
    for field in self.__fields:
        ret.append('- {}:{}{}'.format(
            field.name, ' ' * (mx_fld_n_len + 1 - len(field.name)), field))
    return '\n'.join(ret)

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

def __where(self, set_fields):
    where_clause = [
        '{} {} %s'.format(field.name, field.comp) for field in set_fields]
    return 'where {}'.format(" and ".join(where_clause))

def select(self, *args, **kwargs):
    """Better, still naive implementation of select

    - args are fields names
    - kwargs is a dict of the form {[<field name>:<value>]}
    """
    dct = self.__class__.__dict__
    [dct[field_name].set(value)for field_name, value in kwargs.items()]
    what = '*'
    if args:
        what = ', '.join([dct[field_name].name for field_name in args])
    set_fields = []
    [set_fields.append(field) for field in self.__fields if field.is_set]
    if set_fields:
        where = self.__where(set_fields)
    values = tuple(field.value for field in set_fields)
    self.__cursor.execute(
        "select {} from {} {}".format(what, self.fqtn, where_clause), values)
    return self

def __iter__(self):
    for elt in self.__cursor.fetchall():
        yield elt

def __getitem__(self, key):
    return self.__cursor.fetchall()[key]

interface = {
    '__init__': __init__,
    '__repr__': __repr__,
    '__iter__': __iter__,
    '__getitem__': __getitem__,
    'is_set': is_set,
    '__where': __where,
    'select': select,
    'fields': fields,
}
