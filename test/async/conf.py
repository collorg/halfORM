import pytest_asyncio
from half_orm.async_model import AsyncModel

class ORMContext:
    def __init__(self):
        self.model = AsyncModel("halftest")
        self.pers_cls = None

    async def __aenter__(self):
        await self.model.connect()
        self.pers_cls = self.model.get_relation_class("actor.person")
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.model.disconnect()

@pytest_asyncio.fixture
async def orm_ctx():
    async with ORMContext() as ctx:
        yield ctx