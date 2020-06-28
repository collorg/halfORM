"""This module provides the errors for the model module."""

class MissingConfigFile(Exception):
    """The config file has not been found."""
    def __init__(self, filename):
        self.filename = filename
        Exception.__init__(self, 'Missing config file exception: {}'.format(
            filename))

class MissingParameters(Exception):
    """The database configuration is missing some parameters
    """
    def __init__(self, missing_params, filename=None):
        filename = 'ENVIRONMENT' if filename is None else filename
        super().__init__(
            self,
            ('Missing parameters exception: {}\n'
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
