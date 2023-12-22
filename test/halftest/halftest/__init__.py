"""This module provides the model of the database for the package halftest.
"""

import asyncio
from half_orm.model import load_model

MODEL = asyncio.run(load_model('halftest', scope=__name__))
