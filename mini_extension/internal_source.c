#include <Python.h>

static PyObject* hello_world(PyObject *self, PyObject *args)
{
    return PyUnicode_FromString("Hello World");
}

/* Boilerplate to make a full extension */

static PyMethodDef InternalMethods[] = {
    {"hello_world",  hello_world, METH_NOARGS, "Hello World from an internal C object."},
    {NULL, NULL, 0, NULL}  /* Sentinel */
};

static struct PyModuleDef external_source_module = {
    PyModuleDef_HEAD_INIT,
    "internal",
    NULL,
    -1,
    InternalMethods
};

PyMODINIT_FUNC
PyInit_internal(void)
{
    return PyModule_Create(&external_source_module);
}
