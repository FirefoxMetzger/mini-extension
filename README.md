This project is a minimal demo of how to use poetry to build c extensions.

**Installation**

```
poetry build 
poetry install
```

Explanation: `poetry build` is needed to compile the external C code into a
`.lib` which can be linked to by `external_source.c`. If you don't have to build
a pure c library and just want to build extensions, you don't need this step.

**Usage**

```python
>>> import mini_extension
>>> mini_extension.internal_hello()
'Hello World'
>>> mini_extension.external_hello()
'Hello World from external Code.'
```
