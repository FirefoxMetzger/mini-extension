from ctypes import cdll, c_char_p
from pathlib import Path

library_location = Path(__file__).parent.absolute() / "lib" / "hello_library"
lib_shared_hello = cdll.LoadLibrary(library_location.as_posix())

hello_world = lib_shared_hello.hello
hello_world.restype = c_char_p
