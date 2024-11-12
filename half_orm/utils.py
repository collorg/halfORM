"Various utilities"

import inspect
import os
import re
import sys
from functools import wraps
from keyword import iskeyword

class Color:
    "Colors for the console"
    @staticmethod
    def red(text):
        "red"
        return f"\033[1;31m{text}\033[0m"
    @staticmethod
    def green(text):
        "green"
        return f"\033[1;32m{text}\033[0m"
    @staticmethod
    def blue(text):
        "blue"
        return f"\033[1;34m{text}\033[0m"
    @staticmethod
    def bold(text):
        "bold"
        return f"\033[1m{text}\033[0m"

PWD = os.path.dirname(__file__)
HOP_PATH = os.path.join(PWD, 'packager')
TEMPLATE_DIRS = os.path.join(HOP_PATH, 'templates')

BEGIN_CODE = "#>>> PLACE YOUR CODE BELOW THIS LINE. DO NOT REMOVE THIS LINE!\n"
END_CODE = "#<<< PLACE YOUR CODE ABOVE THIS LINE. DO NOT REMOVE THIS LINE!\n"

def read(file_):
    "Read file helper"
    with open(file_, encoding='utf-8') as text_io_wrapper:
        return text_io_wrapper.read()

def readlines(file_):
    "Return the file split on lines"
    with open(file_, encoding='utf-8') as text_io_wrapper:
        return text_io_wrapper.readlines()

def write(file_, data, mode='w'):
    "Write file helper"
    with open(file_, mode=mode, encoding='utf-8') as text_io_wrapper:
        return text_io_wrapper.write(data)

def hop_version():
    "Returns the version of hop"
    hop_v = None
    with open(os.path.join(HOP_PATH, 'version.txt'), encoding='utf-8') as version:
        hop_v = version.read().strip()
    return hop_v

def error(msg: str, exit_code: int=None):
    "Write error message on stderr and exit if exit is not None"
    sys.stderr.write(f'{Color.bold("HOP ERROR")}: {Color.red(msg)}')
    if exit_code:
        sys.exit(exit_code)

def warning(msg: str):
    "Write warning message on stderr"
    sys.stderr.write(f'{Color.bold("HOP WARNING")}: {msg}')

class TraceDepth: #pragma: no coverage
    "Trace dept class"
    __depth = 0
    on = False

    @classmethod
    def increase(cls):
        "Add 1 to the depth"
        cls.__depth += 1
    @classmethod
    def decrease(cls):
        "Remove 1 from the depth"
        cls.__depth -= 1
    @classmethod
    def depth(cls):
        "Returns the depth"
        return cls.__depth

def trace(fct): #pragma: no coverage
    """Property used to trace the construction of the SQL requests
    """
    @wraps(fct)
    def wrapper(self, *args, **kwargs):
        callerframerecord = inspect.stack()[1]
        frame = callerframerecord[0]
        info = inspect.getframeinfo(frame)
        context = ''
        if info.code_context:
            context = info.code_context[0]
            warn_msg = f'\n{info.filename}:{info.lineno}, in {info.function}\n{context}\n'
        sys.stderr.write(warn_msg)
        TraceDepth.increase()
        res = fct(self, *args, **kwargs)
        TraceDepth.decrease()
        return res
    return wrapper


def _ho_deprecated(fct):
    @wraps(fct)
    def wrapper(*args, **kwargs):
        name = fct.__name__
        ho_name = f'ho_{name}'
        callerframerecord = inspect.stack()[1]
        frame = callerframerecord[0]
        info = inspect.getframeinfo(frame)
        context = ''
        warn_msg = (f'HalfORM WARNING! "{Color.bold(name)}" is deprecated. '
            'It will be removed in half_orm 1.0.\n'
            f'Use "{Color.bold(ho_name)}" instead.\n')
        if info.code_context:
            context = info.code_context[0]
            warn_msg += (f'{info.filename}:{info.lineno}, in {info.function}\n'
                f'{context}\n')
        sys.stderr.write(warn_msg)
        return fct(*args, **kwargs)
    return wrapper

def check_attribute_name(string: str):
    err = None
    if not string.isidentifier():
        error(f'"{Color.bold(string)}" is not a valid identifier in Python.\n')
        err = f'"{string}": not a valid identifier in Python!'
    if iskeyword(string):
        error(f'"{Color.bold(string)}" is a reserved keyword in Python.\n')
        err = f'"{string}": reserved keyword in Python!'
    return err
