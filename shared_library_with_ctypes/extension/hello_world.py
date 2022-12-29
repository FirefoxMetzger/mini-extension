import platform
import os
import re

from ctypes import cdll, c_char_p
from pathlib import Path

# load the library using ctypes
_extension = ''
if platform.system() == ' Windows':
    _extension = 'dll'
if platform.system() == 'Linux':
    _extension = 'so'

_base_path = Path(__file__).parent.absolute().joinpath('lib')
# linux do put 'lib' as name prefix and can put the version after the extension (e.g. libhello_library.so.0.1.0 )
res = [f for f in os.listdir(_base_path) if re.search(rf'[a-z]*hello_library[a_z]*.{_extension}[.0-9]*', f)]

# just one library should be into the folder, otherwise exception is raised
lib_shared_hello = cdll.LoadLibrary(str(_base_path.joinpath(res[0])))

# expose the hello function as hello_world in python
# Note: returns a bytes object, not a python string
hello_world = lib_shared_hello.hello
hello_world.restype = c_char_p
