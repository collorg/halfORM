"""This module provides the errors for the model module."""

class MissingConfigFile(Exception):
    """The config file has not been found."""
    def __init__(self, filename):
        self.filename = filename
        Exception.__init__(self, f'Missing config file exception: {filename}')

class MalformedConfigFile(Exception):
    """The config file is malformed.

    The missing parameters are indicated in the error message.
    """
    def __init__(self, filename, missing_params):
        self.filename = filename
        missing_params_string = '\n - '.join([''] + list(missing_params))
        Exception.__init__(
            self,
            f"Malformed config file exception: {filename}\nMissing parameters: {missing_params_string}")

class UnknownDatabase(Exception):
    """The database dbname couldn't be found. Connexion error ?"""
    def __init__(self, dbname):
        self.dbname = dbname
        Exception.__init__(self, f'Unknown database exception: {dbname}')

class UnknownRelation(Exception):
    """The FQRN doesn't match any relation in the database."""
    def __init__(self, sfqrn):
        self.sfqrn = sfqrn
        Exception.__init__(self, f'Unknown relation exception: {sfqrn}')
