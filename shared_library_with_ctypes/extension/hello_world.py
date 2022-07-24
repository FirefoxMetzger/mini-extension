from ctypes import cdll, c_char_p
from pathlib import Path

# load the library using ctypes
library_location = Path(__file__).parent.absolute() / "lib" / "hello_library"
lib_shared_hello = cdll.LoadLibrary(library_location.as_posix())

# expose the hello function as hello_world in python
# Note: returns a bytes object, not a python string
hello_world = lib_shared_hello.hello
hello_world.restype = c_char_p
