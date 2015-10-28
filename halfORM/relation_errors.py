class ExpectedOneError(Exception):
    def __init__(self, relation, count):
        plural = count == 0 and '' or 's'
        Exception.__init__(self, 'Expected 1, got {} tuple{}:\n{}'.format(
            count, plural, relation))
