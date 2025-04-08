#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import typing
from configparser import ConfigParser

import psycopg

from half_orm import pg_meta
from .base_model import BaseModel



class AsyncModel(BaseModel):
    def __init__(self, config_file: str, scope: str = None):
        super().__init__(config_file, scope)
        self.__conn = None
        self._pg_meta = None

    async def connect(self, reload: bool = False):
        await self.disconnect()
        self.__conn = await psycopg.AsyncConnection.connect(**self._dbinfo, row_factory=psycopg.rows.dict_row)
        self._pg_meta = pg_meta.PgMeta(self.__conn, reload)
        if reload:
            self._classes_[self._dbname] = {}
        if self._dbname not in self.__class__._deja_vu:
            self._deja_vu[self._dbname] = self

    async def reconnect(self):
        await self.connect(reload=True)

    async def disconnect(self):
        conn = self.__conn
        if conn is not None and not conn.closed:
            await conn.close()

    async def ping(self) -> bool:
        try:
            await self.execute_query("SELECT 1")
            return True
        except (psycopg.errors.OperationalError, psycopg.errors.InterfaceError):
            try:
                await self.connect()
                await self.execute_query("SELECT 1")
            except Exception as exc:
                sys.stderr.write(f"{exc}\n")
                sys.stderr.flush()
            return False

    async def execute_query(self, query: str, values: typing.Sequence = ()):
        async with self.__conn.cursor() as cursor:
            try:
                await cursor.execute(query, values)
            except (psycopg.errors.OperationalError, psycopg.errors.InterfaceError):
                await self.ping()
                async with self.__conn.cursor() as cursor2:
                    await cursor2.execute(query, values)
                    return await cursor2.fetchall()
            return await cursor.fetchall()

    async def execute_function(self, func_name: str, *args, **kwargs):
        if bool(args) and bool(kwargs):
            raise RuntimeError("You can't mix args and kwargs with the execute_function method!")
        async with self.__conn.cursor() as cursor:
            if kwargs:
                params = ', '.join(f"%({k})s" for k in kwargs.keys())
                query = f"SELECT * FROM {func_name}({params})"
                await cursor.execute(query, kwargs)
            else:
                params = ', '.join(['%s' for _ in args])
                query = f"SELECT * FROM {func_name}({params})"
                await cursor.execute(query, args)
            try:
                return await cursor.fetchall()
            except psycopg.ProgrammingError:
                return None

    async def call_procedure(self, proc_name: str, *args, **kwargs):
        if bool(args) and bool(kwargs):
            raise RuntimeError("You can't mix args and kwargs with the call_procedure method!")
        async with self.__conn.cursor() as cursor:
            if kwargs:
                params = ', '.join(f"%({k})s" for k in kwargs.keys())
                query = f"CALL {proc_name}({params})"
                await cursor.execute(query, kwargs)
            else:
                params = ', '.join(['%s' for _ in args])
                query = f"CALL {proc_name}({params})"
                await cursor.execute(query, args)

    @property
    async def _connection(self):
        return self.__conn
