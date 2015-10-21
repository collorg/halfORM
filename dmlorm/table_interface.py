def __init__(self, **kwargs):
    self.__cursor = self.model.cursor()
    for field_name, value in kwargs.items():
        self.__class__.__dict__[field_name].set(value)

def __repr__(self):
    tks = {'r': 'TABLE', 'v': 'VIEW'}
    table_kind = tks.get(self.__kind, "UNKNOWN TYPE")
    ret = [60*'-']
    ret.append("{}: {}".format(table_kind, self.fqtn))
    ret.append(('- cluster: {dbname}\n'
                '- schema:  {schemaname}\n'
                '- table:   {tablename}').format(**vars(self.__class__)))
    ret.append('FIELDS:')
    for field in self.__fields:
        ret.append('- {}'.format(field))
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

def select(self):
    """First naive implementation of select"""
    set_fields = []
    for field in self.__fields:
        if field.is_set:
            set_fields.append(field)
    where_clause = [
        '{} {} %s'.format(field.sql_name, field.comp) for field in set_fields]
    if where_clause:
        where_clause = 'where {}'.format(" and ".join(where_clause))
    values = tuple(field.value for field in set_fields)
    print(values)
    self.__cursor.execute(
        "select * from {} {}".format(self.fqtn, where_clause), values)
    return self

def __iter__(self):
    for elt in self.__cursor.fetchall():
        celt = {'{}_'.format(key):value for key, value in elt.items()}
        yield celt

def __getitem__(self, key):
    return self.__cursor.fetchall()[key]

interface = {
    '__init__': __init__,
    '__repr__': __repr__,
    '__iter__': __iter__,
    '__getitem__': __getitem__,
    'is_set': is_set,
    'select': select,
    'fields': fields,
}
