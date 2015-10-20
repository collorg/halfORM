def __init__(self, **kwargs):
    """Fields init with kwargs"""

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

interface = {
    '__init__': __init__,
    '__repr__': __repr__,
}
