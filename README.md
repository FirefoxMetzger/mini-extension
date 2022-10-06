This project is a collection of examples on how to build various types of C code
from poetry. The following examples are currently included:

- **extension_only**: A C extension that has no external dependencies.
- **external_archive**: A C extension that depends on an external C library
  (statically linked).
- **shared_library_with_ctypes**: A shared library (.dll/.so) that is accessed
  using ctypes.

**Installation**

After cloning the repo, simply `cd` into the example folder and call 
`poetry install` as usual. 

(Tested with poetry version 1.1.14 on Windows and MSVC)

**Usage**

Each example is used the same way:

```python
>>> from extension.hello_world import hello_world
>>> hello_world()
"Hello World"  # extension_only
"Hello World from external C archvive."  # external_archive
b"Hello World from a shared C library via ctypes."  # shared_library_with_ctypes
```

**Questions, Features, Bugs**

Please open a new issue to discuss any problems, features, bugs, questions, etc.


**VSCode debug config**

Not sure where exactly to put this, but it is too useful to not mention/document. 
If you are using VSCode while working with poetry and C extensions it can be 
useful to be able to step through your `build.py` in the debugger. To do so, you
can use a configuration like the one below:

```
    "configurations": [
        {
            "name": "Poetry Build",
            "type": "python",
            // path to the python executable used by poetry (NOT the one in the project's venv)
            "python": "C:\\Users\\Sebastian\\AppData\\Roaming\\pypoetry\\venv\\Scripts\\python.exe",
            "request": "launch",
            "module": "poetry",
            "args": ["build"],
            "console": "integratedTerminal",
        },
    ]
```
