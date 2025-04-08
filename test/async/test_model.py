import pytest
import pytest_asyncio
import asyncio
from unittest import TestCase

from ..init import model, async_model as a_model

@pytest_asyncio.fixture
async def connected_model():
    await a_model.connect()
    yield a_model
    await a_model.disconnect()

@pytest.mark.asyncio
class TestAsync:
    async def test_async_connection(self, connected_model):
        connection = await connected_model._connection
        assert connection is not None
        assert not connection.closed
        await connected_model.disconnect()
        connection = await connected_model._connection
        assert connection.closed

    async def test_async_query_execution(self, connected_model):
        rows = await connected_model.execute_query("SELECT 1 AS test_value")
        assert len(rows) == 1
        assert rows[0]["test_value"] == 1

    async def test_repr(self, connected_model):
        TestCase().assertEqual(model.desc(), connected_model.desc())
        
    async def test_connect_twice(self, connected_model):
        await connected_model.connect(reload=True)
        conn = await connected_model._connection
        assert conn is not None