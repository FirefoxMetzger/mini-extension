#include <Python.h>
#include "hello.h"

static PyObject* hello_world(PyObject *self, PyObject *args)
{
    return PyUnicode_FromString(hello());
}

/* Boilerplate to make a full extension */

static PyMethodDef InternalMethods[] = {
    {"hello_world",  hello_world, METH_NOARGS, "Hello World from external C source."},
    {NULL, NULL, 0, NULL}  /* Sentinel */
};

static struct PyModuleDef hello_world_module = {
    PyModuleDef_HEAD_INIT,
    "external",
    NULL,
    -1,
    InternalMethods
};

PyMODINIT_FUNC
PyInit_hello_world(void)
{
    return PyModule_Create(&hello_world_module);
}
