#!/usr/bin/env python3
#-*- coding:  utf-8 -*-

import contextlib
import io
import re

import sys
from unittest import TestCase
from time import sleep
from random import randint
import pytest
import pytest_asyncio
from ..init import halftest

import psycopg

from half_orm import relation_errors
from half_orm.async_transaction import AsyncTransaction
from half_orm.async_model import AsyncModel

# @pytest_asyncio.fixture
# async def connected_model():
#     await a_model.connect()
#     pers_cls = a_model.get_relation_class('actor.person')
#     yield a_model, pers_cls
#     await a_model.disconnect()

@pytest.mark.asyncio
class Test:
    async def test_count(self):
        async_model = AsyncModel('halftest')
        await async_model.connect()
        pers_cls = async_model.get_relation_class('actor.person')
        assert pers_cls().ho_count() == 60

    async def test_expected_one_error_0(self):
        async_model = AsyncModel('halftest')
        await async_model.connect()
        pers_cls = async_model.get_relation_class('actor.person')
        pers = pers_cls(last_name="this name doesn't exist")
        with pytest.raises(relation_errors.ExpectedOneError):
            pers.ho_get()

    async def test_expected_one_error_many(self):
        async_model = AsyncModel('halftest')
        await async_model.connect()
        pers_cls = async_model.get_relation_class('actor.person')
        pers = pers_cls()
        with pytest.raises(relation_errors.ExpectedOneError):
            pers.ho_get()

    async def test_insert_error(self):
        async_model = AsyncModel('halftest')
        await async_model.connect()
        pers_cls = async_model.get_relation_class('actor.person')
        pers = pers_cls(last_name='ba')
        assert pers.ho_count() == 1
        pers = pers.ho_get()
        with pytest.raises(psycopg.errors.UniqueViolation):
            await pers.ho_insert()

    async def test_select(self):
        async_model = AsyncModel('halftest')
        await async_model.connect()
        pers_cls = async_model.get_relation_class('actor.person')
        n = 'abcdef'[randint(0, 5)]
        p = chr(ord('a') + range(10)[randint(0, 9)])
        pers = pers_cls(
            last_name=('ilike', f'{n}%'),
            first_name=('ilike', f'%{p}'),
            birth_date=halftest.today)
        for dct in pers:
            pers_cls(**dct).ho_get()

    async def test_update(self):
        async_model = AsyncModel('halftest')
        await async_model.connect()
        pers_cls = async_model.get_relation_class('actor.person')
        pers = pers_cls(last_name=('like', 'a%'))
        assert pers.ho_count() == 10
        def update(pers, fct):
            for elt in pers:
                pers = pers_cls(**elt)
                pers.ho_update(last_name=fct(pers.last_name.value), first_name=None)

        update(pers, str.upper)
        pers = pers_cls(last_name=('like', 'A%'))
        assert pers.ho_count() == 10
        async with AsyncTransaction(async_model):
            update(pers, str.lower)

    async def test_update_none_values_are_removed(self):
        "it should remove None values before update"
        async_model = AsyncModel('halftest')
        await async_model.connect()
        pers_cls = async_model.get_relation_class('actor.person')
        f1 = io.StringIO()
        value1 = ''
        with contextlib.redirect_stdout(f1):
            pers_cls(last_name='Un test').ho_update()
            value1 = re.sub(r'\s+', ' ', f1.getvalue().replace('\n', ' ').replace('  ', ' '))

        f2 = io.StringIO()
        value2 = ''
        with contextlib.redirect_stdout(f2):
            pers_cls(last_name='Un test', first_name=None).ho_update()
            value2 = re.sub(r'\s+', ' ', f2.getvalue().replace('\n', ' ').replace('  ', ' '))
        assert value1 == value2

    async def test_update_with_none_values(self):
        "it should return None (do nothing) if no update values are provided."
        async_model = AsyncModel('halftest')
        await async_model.connect()
        pers_cls = async_model.get_relation_class('actor.person')
        pers = pers_cls(last_name=None, first_name=None, birth_date=None)
        res = pers.ho_update(update_all=True)
        assert res is None
