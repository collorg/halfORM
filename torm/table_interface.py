def __init__(self, **kwargs):
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

def select(self):
    raise NotImplementedError

interface = {
    '__init__': __init__,
    '__repr__': __repr__,
    'select': select,
    'is_set': is_set,
}
