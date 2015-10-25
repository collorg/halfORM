class MissingConfigFile(Exception):
    def __init__(self, filename):
        self.filename = filename
        Exception.__init__(self, 'Missing config file exception: {}'.format(
            filename))

class MalformedConfigFile(Exception):
    def __init__(self, filename, missing_params):
        self.filename = filename
        Exception.__init__(
            self,
            ('Malformed config file exception: {}\n'
             'Missing parameters: {}').format(
                 filename, '\n - '.join([''] + list(missing_params))))

class UnknownDatabase(Exception):
    def __init__(self, dbname):
        self.dbname = dbname
        Exception.__init__(self, 'Unknown database exception: {}'.format(
            dbname))

class UnknownRelation(Exception):
    def __init__(self, sfqtn):
        self.sfqtn = sfqtn
        Exception.__init__(self, 'Unknown relation exception: {}'.format(
            sfqtn))
