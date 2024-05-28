from half_orm.field import Field

class TextField(Field):
    def __init__(self, name, relation, metadata):
        super().__init__(name, relation, metadata)
