#include <Python.h>
#include <gp_Pnt2d.hxx>

namespace {

PyObject* make_point(PyObject*, PyObject* args)
{
    double x = 0.0;
    double y = 0.0;
    if (!PyArg_ParseTuple(args, "dd", &x, &y)) {
        return nullptr;
    }

    gp_Pnt2d point(x, y);
    return Py_BuildValue("(dd)", point.X(), point.Y());
}

PyObject* describe_point(PyObject*, PyObject* args)
{
    double x = 0.0;
    double y = 0.0;
    if (!PyArg_ParseTuple(args, "dd", &x, &y)) {
        return nullptr;
    }

    gp_Pnt2d point(x, y);
    return PyUnicode_FromFormat("gp_Pnt2d(X=%f, Y=%f)", point.X(), point.Y());
}

PyMethodDef TestMethods[] = {
    {"make_point", make_point, METH_VARARGS, "Create a gp_Pnt2d and return its coordinates."},
    {"describe_point", describe_point, METH_VARARGS, "Create a gp_Pnt2d and return a string description."},
    {nullptr, nullptr, 0, nullptr}
};

PyModuleDef TestModule = {
    PyModuleDef_HEAD_INIT,
    "SpringTest",
    "Python bindings for simple gp_Pnt2d helpers.",
    -1,
    TestMethods,
    nullptr,
    nullptr,
    nullptr,
    nullptr
};

} // namespace

PyMODINIT_FUNC PyInit_SpringTest(void)
{
    return PyModule_Create(&TestModule);
}
