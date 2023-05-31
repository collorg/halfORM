#!/usr/bin/env python

import os
import sys

TEMPLATE = [
"""from typing import Union, Any
import uuid
from litestar import Request, Litestar, get, post, patch, put, delete
from pydantic import BaseModel

app = Litestar()
"""]

IMPORT_TEMPLATE = """

from {module} import {relation.__name__}

'''{doc}
'''
"""

GET_TEMPLATE = """

@{method_l}("/{path}")
async def {method_l}_{fct_suffix}(request: Request, query: dict[str, Any]) -> dict:
    return {relation.__name__}().{method}(**query)

app.register({method_l}_{fct_suffix})
"""

POST_TEMPLATE = """

@{method_l}("/{path}")
async def {method_l}_{fct_suffix}(request: Request, query: dict[str, Any]) -> dict:
    json = await request.json()
    return {relation.__name__}().{method}(**json)

app.register({method_l}_{fct_suffix})
"""

PATCH_TEMPLATE = """

@{method_l}("/{path}/{{id: uuid}}")
async def {method_l}_{fct_suffix}(request: Request, id: uuid.UUID, query: dict[str, Any]) -> dict:
    json = await(request.json())
    return {relation.__name__}(id=id).{method}(**json)

app.register({method_l}_{fct_suffix})
"""

PUT_TEMPLATE = """

@{method_l}("/{path}/{{id: uuid}}")
async def {method_l}_{fct_suffix}(request: Request, id: uuid.UUID, query: dict[str, Any]) -> dict:
    json = await(request.json())
    return {relation.__name__}(id=id).{method}(**json)

app.register({method_l}_{fct_suffix})
"""

DELETE_TEMPLATE = """

@{method_l}("/{path}/{{id: uuid}}")
async def {method_l}_{fct_suffix}(request: Request) -> dict:
    return {relation.__name__}(id=id).{method}()

app.register({method_l}_{fct_suffix})
"""

templates = {
    'POST': POST_TEMPLATE,
    'GET': GET_TEMPLATE,
    'PATCH': PATCH_TEMPLATE,
    'PUT': PUT_TEMPLATE,
    'DELETE': DELETE_TEMPLATE
}

class Api:
    def __init__(self, repo=None):
        self.__repo = repo

    def generate(self):
        "Generates the API"
        params = {
            'dbname': self.__repo.name,
        }

        for relation, relation_type in self.__repo.model.classes():
            module = relation.__module__
            sys.stderr.write(f'{module}: {relation_type}\n')
            methods = []
            for key in ['GET', 'POST', 'PATCH', 'PUT', 'DELETE']:
                if not ((hasattr(relation, key) and callable(getattr(relation, key)))):
                    continue
                methods.append(key)
            if not methods:
                continue
            doc = relation.ho_description()
            TEMPLATE.append(IMPORT_TEMPLATE.format(relation=relation, module=module, doc=doc))
            for method in methods:
                fct_suffix = module.replace('.', '_')
                path = module.replace('.', '/')
                params.update({
                    'method': method,
                    'method_l': method.lower(),
                    'path': path,
                    'fct_suffix': fct_suffix,
                    'relation': relation
                })
                TEMPLATE.append(templates[method].format(**params))
        api_dir = f'{self.__repo.base_dir}/Api/'
        if not os.path.exists(api_dir):
            os.mkdir(api_dir)
        with open(f'{api_dir}/main.py', 'w', encoding='UTF8') as main:
            main.write(''.join(TEMPLATE))
