#include "SpringGui.h"

#include <Python.h>

static PyMethodDef SpringGui_methods[] = {
    {nullptr, nullptr, 0, nullptr}
};

static struct PyModuleDef SpringGui_module = {
    PyModuleDef_HEAD_INIT,
    "SpringGui",
    "FreeCAD Spring GUI bindings",
    -1,
    SpringGui_methods,
    nullptr,
    nullptr,
    nullptr,
    nullptr
};

PyMODINIT_FUNC PyInit_SpringGui(void)
{
    SpringGui::initModule();
    return PyModule_Create(&SpringGui_module);
}

