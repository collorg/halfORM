"""This module provides the errors for the model module."""

class MissingConfigFile(Exception):
    """The config file has not been found."""
    def __init__(self, filename):
        self.filename = filename
        Exception.__init__(self, f'Missing config file: {filename}')

class MalformedConfigFile(Exception):
    """The config file is malformed.

    The missing parameters are indicated in the error message.
    """
    def __init__(self, filename, msg, missing_param):
        self.filename = filename
        Exception.__init__(
            self,
            f"Malformed config file: {filename}\n{msg}: {missing_param}")

class UnknownRelation(Exception):
    """The FQRN doesn't match any relation in the database."""
    def __init__(self, sfqrn):
        self.dbname = sfqrn[0]
        self.schema = sfqrn[1]
        self.relation = sfqrn[2]
        Exception.__init__(self, f"'{sfqrn[1]}.{sfqrn[2]}' does not exist in the database {sfqrn[0]}.")

class MissingSchemaInName(Exception):
    """The QRN should contain a schema name."""
    def __init__(self, qrn):
        Exception.__init__(self, f"do you mean 'public.{qrn}'?")
