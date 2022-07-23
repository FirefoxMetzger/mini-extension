#include <Python.h>
#include "external_shared/hello.h"

static PyObject* hello_world(PyObject *self, PyObject *args)
{
    return PyUnicode_FromString(hello());
}

/* Boilerplate to make a full extension */

static PyMethodDef InternalMethods[] = {
    {"hello_world",  hello_world, METH_NOARGS, "Hello World from external C source."},
    {NULL, NULL, 0, NULL}  /* Sentinel */
};

static struct PyModuleDef external_source_module = {
    PyModuleDef_HEAD_INIT,
    "external",
    NULL,
    -1,
    InternalMethods
};

PyMODINIT_FUNC
PyInit_external(void)
{
    return PyModule_Create(&external_source_module);
}
