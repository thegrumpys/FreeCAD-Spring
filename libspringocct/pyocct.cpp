// SPDX-License-Identifier: BSD-3-Clause

#include "Pnt2dNative.hpp"

#include <pybind11/pybind11.h>
#include <pybind11/operators.h>
#include <pybind11/stl.h>

#include <gp_Pnt2d.hxx>
#include <gp_Vec2d.hxx>

#include <string>

namespace py = pybind11;

PYBIND11_MODULE(springocct, m)
{
    m.doc() = "Python bindings for a minimal set of OpenCascade helpers";

    py::class_<gp_Pnt2d>(m, "Pnt2d")
        .def(py::init<>())
        .def(py::init<double, double>(), py::arg("x"), py::arg("y"))
        .def_property("x", &gp_Pnt2d::X, &gp_Pnt2d::SetX, "X coordinate")
        .def_property("y", &gp_Pnt2d::Y, &gp_Pnt2d::SetY, "Y coordinate")
        .def(
            "set_coord",
            [](gp_Pnt2d& point, double x, double y) {
                point.SetCoord(x, y);
            },
            py::arg("x"),
            py::arg("y"),
            "Set both coordinates at once"
        )
        .def("coord", [](const gp_Pnt2d& point) { return py::make_tuple(point.X(), point.Y()); }, "Return coordinates as a tuple")
        .def(
            "translated",
            [](const gp_Pnt2d& point, double dx, double dy) {
                return point.Translated(gp_Vec2d(dx, dy));
            },
            py::arg("dx"),
            py::arg("dy"),
            "Return a translated copy"
        )
        .def(
            "distance",
            [](const gp_Pnt2d& self, const gp_Pnt2d& other) {
                return self.Distance(other);
            },
            py::arg("other"),
            "Distance to another point"
        )
        .def(
            "is_equal",
            [](const gp_Pnt2d& self, const gp_Pnt2d& other, double linear_tolerance) {
                return self.IsEqual(other, linear_tolerance);
            },
            py::arg("other"),
            py::arg("tolerance"),
            "Check equality with a tolerance"
        )
        .def(
            "mirror",
            [](const gp_Pnt2d& self, const gp_Pnt2d& about) {
                return self.Mirrored(about);
            },
            py::arg("about"),
            "Mirror the point about another point"
        )
        .def("__repr__", [](const gp_Pnt2d& point) {
            return "Pnt2d(x=" + std::to_string(point.X()) + ", y=" + std::to_string(point.Y()) + ")";
        });

    m.def(
        "distance",
        &Distance2d,
        py::arg("first"),
        py::arg("second"),
        "Compute the distance between two points"
    );
}
