import platform
import os
import re

from ctypes import cdll, c_char_p
from pathlib import Path

# load the library using ctypes
_extension = ''
if platform.system() == ' Windows':
    _extension = 'dll'
elif platform.system() == 'Linux':
    _extension = 'so'

_base_path = Path(__file__).parent.absolute().joinpath('lib')
# linux do put 'lib' as name prefix and can put the version after the extension (e.g. libhello_library.so.0.1.0 )
res = [f for f in os.listdir(_base_path) if re.search(rf'[a-z]*hello_library[a_z]*.{_extension}[.0-9]*', f)]

# just one library should be into the folder, otherwise exception is raised
lib_shared_hello = cdll.LoadLibrary((_base_path / res[0]).as_posix())

# expose the hello function as hello_world in python
_hello_world = lib_shared_hello.hello
_hello_world.restype = c_char_p


def hello_world():
    """Prints a hello world message.

    In ctypes, a C string is given to python as a `bytes()` object. This wrapper
    converts it into the expected string object.
    
    """

    return _hello_world().decode()
