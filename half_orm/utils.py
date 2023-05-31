"Various utilities"

import os
import sys
from functools import wraps

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
    sys.stderr.write(Color.bold(f'HOP WARNING: {msg}'))

trace_depth = 0
def trace(fct):
    @wraps(fct)
    def wrapper(self, *args, **kwargs):
        global trace_depth
        name = fct.__name__
        print(f'{" " * trace_depth}>>[{trace_depth}]>> {name}')
        trace_depth += 1
        res = fct(self, *args, **kwargs)
        trace_depth -= 1
        return res
    return wrapper

