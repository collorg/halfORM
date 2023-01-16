"Various utilities"

import os
import sys

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

HOP_PATH = os.path.dirname(__file__)
TEMPLATE_DIRS = os.path.join(HOP_PATH, 'templates')

BEGIN_CODE = "#>>> PLACE YOUR CODE BELLOW THIS LINE. DO NOT REMOVE THIS LINE!\n"
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
    "Write error message on stderr in bold red and exit if exit is not None"
    sys.stderr.write(f'\033[1mHOP ERROR\033[0m: {Color.red(msg)}')
    if exit_code:
        sys.exit(exit_code)
