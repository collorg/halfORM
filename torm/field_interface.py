def __init__(self, name, metadata):
    self.__name = name
    self.__metadata = metadata
    self.__is_set = False
    self.__value = None
    self.__comp = '='

def __repr__(self):
    md = self.__metadata
    return "{}: ({}) {}".format(
        self.__name, md['fieldtype'], md['pkey'] and 'PK' or (
            '{}{}'.format(
                md['uniq'] and 'UNIQ ' or '',
                md['notnull'] and 'NOT NULL' or '')))

@property
def is_set(self):
    return self.__is_set

def get(self):
    return self.__value

def set(self, value, comp=None):
    if type(value) is tuple:
        assert len(value) == 2
        value, comp = value
    if value is None and comp is None:
        comp = 'is'
    if value is None:
        assert comp == 'is' or comp == 'is not'
    elif comp is None:
        comp = '='
    self.__is_set = True
    self.__value = value
    self.__comp = comp

value = property(get, set)

@property
def comp(self):
    return self.__comp

interface = {
    '__init__': __init__,
    '__repr__': __repr__,
    'is_set': is_set,
    'get': get,
    'set': set,
    'value': value,
    'comp': comp,
}
