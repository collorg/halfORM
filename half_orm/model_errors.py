"""This module provides the errors for the model module."""

class MissingConfigFile(Exception):
    """The config file has not been found."""
    def __init__(self, filename):
        self.filename = filename
        Exception.__init__(self, 'Missing config file exception: {}'.format(
            filename))

class MalformedConfigFile(Exception):
    """The config file is malformed.

    The missing parameters are indicated in the error message.
    """
    def __init__(self, filename, missing_params):
        self.filename = filename
        Exception.__init__(
            self,
            ('Malformed config file exception: {}\n'
             'Missing parameters: {}').format(
                 filename, '\n - '.join([''] + list(missing_params))))

class UnknownDatabase(Exception):
    """The database dbname couldn't be found. Connexion error ?"""
    def __init__(self, dbname):
        self.dbname = dbname
        Exception.__init__(self, 'Unknown database exception: {}'.format(
            dbname))

class UnknownRelation(Exception):
    """The FQRN doesn't match any relation in the database."""
    def __init__(self, sfqrn):
        self.sfqrn = sfqrn
        Exception.__init__(self, 'Unknown relation exception: {}'.format(
            sfqrn))
