def __init__(self, name, metadata):
    self.__name = name
    self.__metadata = metadata

def __repr__(self):
    md = self.__metadata
    return "{}: ({}) {}".format(
        self.__name,
        md['fieldtype'],
        md['pkey'] and 'PK' or (
            '{}{}'.format(md['uniq'] and 'UNIQ ' or '',
                           md['notnull'] and 'NOT NULL' or '')))

interface = {
    '__init__': __init__,
    '__repr__': __repr__,
}
