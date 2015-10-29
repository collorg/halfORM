import sys

class Transaction():
    __level = 0
    def __init__(self, func):
        self.__func = func

    def __call__(self, relation, *args, **kwargs):
        res = None
        try:
            Transaction.__level += 1
            if relation.model.connection.autocommit:
                relation.model.connection.autocommit = False
            res = self.__func(relation, *args, **kwargs)
            Transaction.__level -= 1
            if Transaction.__level == 0:
                relation.model.connection.commit()
                relation.model.connection.autocommit = True
        except Exception as err:
            sys.stderr.write(
                "Transaction error: {}\nRolling back!\n".format(err))
            self.__level = 0
            relation.model.connection.rollback()
            relation.model.connection.autocommit = True
            raise err
        return res
