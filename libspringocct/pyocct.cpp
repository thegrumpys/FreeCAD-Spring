// SPDX-License-Identifier: BSD-3-Clause

#include <Python.h>

#include <pybind11/pybind11.h>
#include <pybind11/operators.h>
#include <pybind11/stl.h>

#include "Pnt2dNative.hpp"

#include <GCE2d_MakeLine.hxx>
#include <Geom2d_Line.hxx>
#include <gp_Ax1.hxx>
#include <gp_Ax2.hxx>
#include <gp_Ax3.hxx>
#include <gp_Circ.hxx>
#include <gp_Dir.hxx>
#include <gp_Dir2d.hxx>
#include <gp_Lin2d.hxx>
#include <gp_Pnt.hxx>
#include <gp_Pnt2d.hxx>
#include <gp_Vec.hxx>
#include <gp_Vec2d.hxx>

#include <Mod/Part/App/TopoShape.h>

#include <string>
#include <stdexcept>

#include <Standard_Handle.hxx>

struct check_pyobject_type {
    check_pyobject_type() {
        std::cout << "C++ thinks PyObject is: " << typeid(PyObject).name() << "\n";
    }
} check_instance;

namespace py = pybind11;

PYBIND11_DECLARE_HOLDER_TYPE(T, opencascade::handle<T>);

PYBIND11_MODULE(springocct, m)
{
    m.doc() = "Python bindings for a minimal set of OpenCascade helpers";

    py::class_<gp_Lin2d>(m, "Lin2d")
        .def(py::init<>())
        .def(py::init<const gp_Pnt2d&, const gp_Dir2d&>(), py::arg("location"), py::arg("direction"))
        .def_property("location", &gp_Lin2d::Location, &gp_Lin2d::SetLocation, "Line origin")
        .def_property("direction", &gp_Lin2d::Direction, &gp_Lin2d::SetDirection, "Line direction")
        .def("reverse", &gp_Lin2d::Reverse, "Reverse the line orientation")
        .def("__repr__", [](const gp_Lin2d& line) {
            const auto loc = line.Location();
            const auto dir = line.Direction();
            return "Lin2d(location=(" + std::to_string(loc.X()) + ", " + std::to_string(loc.Y())
                   + "), direction=(" + std::to_string(dir.X()) + ", " + std::to_string(dir.Y()) + "))";
        });

    py::class_<gp_Dir2d>(m, "Dir2d")
        .def(py::init<>())
        .def(py::init<double, double>(), py::arg("x"), py::arg("y"))
        .def_property("x", &gp_Dir2d::X, &gp_Dir2d::SetX, "X component")
        .def_property("y", &gp_Dir2d::Y, &gp_Dir2d::SetY, "Y component")
        .def("coord", [](const gp_Dir2d& dir) { return py::make_tuple(dir.X(), dir.Y()); }, "Return components as a tuple")
        .def("reversed", [](const gp_Dir2d& dir) { return dir.Reversed(); }, "Return a reversed direction")
        .def("__repr__", [](const gp_Dir2d& dir) {
            return "Dir2d(x=" + std::to_string(dir.X()) + ", y=" + std::to_string(dir.Y()) + ")";
        });

    py::class_<gp_Vec2d>(m, "Vec2d")
        .def(py::init<>())
        .def(py::init<double, double>(), py::arg("x"), py::arg("y"))
        .def_property("x", &gp_Vec2d::X, &gp_Vec2d::SetX, "X component")
        .def_property("y", &gp_Vec2d::Y, &gp_Vec2d::SetY, "Y component")
        .def("coord", [](const gp_Vec2d& vec) { return py::make_tuple(vec.X(), vec.Y()); }, "Return components as a tuple")
        .def("magnitude", &gp_Vec2d::Magnitude, "Vector magnitude")
        .def("normalized", [](const gp_Vec2d& vec) { return vec.Normalized(); }, "Return a normalized copy")
        .def("__repr__", [](const gp_Vec2d& vec) {
            return "Vec2d(x=" + std::to_string(vec.X()) + ", y=" + std::to_string(vec.Y()) + ")";
        });

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

    py::class_<gp_Pnt>(m, "Pnt")
        .def(py::init<>())
        .def(py::init<double, double, double>(), py::arg("x"), py::arg("y"), py::arg("z"))
        .def_property("x", &gp_Pnt::X, &gp_Pnt::SetX, "X coordinate")
        .def_property("y", &gp_Pnt::Y, &gp_Pnt::SetY, "Y coordinate")
        .def_property("z", &gp_Pnt::Z, &gp_Pnt::SetZ, "Z coordinate")
        .def("coord", [](const gp_Pnt& point) { return py::make_tuple(point.X(), point.Y(), point.Z()); }, "Return coordinates as a tuple")
        .def("distance", [](const gp_Pnt& self, const gp_Pnt& other) { return self.Distance(other); }, py::arg("other"), "Distance to another point")
        .def("translated", [](const gp_Pnt& point, const gp_Vec& vec) { return point.Translated(vec); }, py::arg("vec"), "Return translated point")
        .def("__repr__", [](const gp_Pnt& point) {
            return "Pnt(x=" + std::to_string(point.X()) + ", y=" + std::to_string(point.Y()) + ", z=" + std::to_string(point.Z()) + ")";
        });

    py::class_<gp_Dir>(m, "Dir")
        .def(py::init<>())
        .def(py::init<double, double, double>(), py::arg("x"), py::arg("y"), py::arg("z"))
        .def_property("x", &gp_Dir::X, &gp_Dir::SetX, "X component")
        .def_property("y", &gp_Dir::Y, &gp_Dir::SetY, "Y component")
        .def_property("z", &gp_Dir::Z, &gp_Dir::SetZ, "Z component")
        .def("coord", [](const gp_Dir& dir) { return py::make_tuple(dir.X(), dir.Y(), dir.Z()); }, "Return components as a tuple")
        .def("reversed", [](const gp_Dir& dir) { return dir.Reversed(); }, "Return a reversed direction")
        .def("__repr__", [](const gp_Dir& dir) {
            return "Dir(x=" + std::to_string(dir.X()) + ", y=" + std::to_string(dir.Y()) + ", z=" + std::to_string(dir.Z()) + ")";
        });

    py::class_<gp_Vec>(m, "Vec")
        .def(py::init<>())
        .def(py::init<double, double, double>(), py::arg("x"), py::arg("y"), py::arg("z"))
        .def(py::init<const gp_Pnt&, const gp_Pnt&>(), py::arg("start"), py::arg("end"))
        .def_property("x", &gp_Vec::X, &gp_Vec::SetX, "X component")
        .def_property("y", &gp_Vec::Y, &gp_Vec::SetY, "Y component")
        .def_property("z", &gp_Vec::Z, &gp_Vec::SetZ, "Z component")
        .def("coord", [](const gp_Vec& vec) { return py::make_tuple(vec.X(), vec.Y(), vec.Z()); }, "Return components as a tuple")
        .def("magnitude", &gp_Vec::Magnitude, "Vector magnitude")
        .def("normalized", [](const gp_Vec& vec) { return vec.Normalized(); }, "Return a normalized copy")
        .def("__repr__", [](const gp_Vec& vec) {
            return "Vec(x=" + std::to_string(vec.X()) + ", y=" + std::to_string(vec.Y()) + ", z=" + std::to_string(vec.Z()) + ")";
        });

    py::class_<gp_Ax2>(m, "Ax2")
        .def(py::init<>())
        .def(py::init<const gp_Pnt&, const gp_Dir&>(), py::arg("location"), py::arg("direction"))
        .def(py::init<const gp_Pnt&, const gp_Dir&, const gp_Dir&>(), py::arg("location"), py::arg("direction"), py::arg("x_direction"))
        .def_property("location", &gp_Ax2::Location, &gp_Ax2::SetLocation, "Axis origin")
        .def_property("direction", &gp_Ax2::Direction, &gp_Ax2::SetDirection, "Main direction")
        .def_property("x_direction", &gp_Ax2::XDirection, &gp_Ax2::SetXDirection, "X direction")
        .def_property("y_direction", &gp_Ax2::YDirection, &gp_Ax2::SetYDirection, "Y direction")
        .def("axis", &gp_Ax2::Axis, "Return axis as gp_Ax1")
        .def("__repr__", [](const gp_Ax2& axis) {
            const auto loc = axis.Location();
            const auto dir = axis.Direction();
            return "Ax2(location=(" + std::to_string(loc.X()) + ", " + std::to_string(loc.Y()) + ", " + std::to_string(loc.Z()) + ")"
                   ", direction=(" + std::to_string(dir.X()) + ", " + std::to_string(dir.Y()) + ", " + std::to_string(dir.Z()) + "))";
        });

    py::class_<gp_Ax3>(m, "Ax3")
        .def(py::init<>())
        .def(py::init<const gp_Pnt&, const gp_Dir&>(), py::arg("location"), py::arg("direction"))
        .def(py::init<const gp_Pnt&, const gp_Dir&, const gp_Dir&>(), py::arg("location"), py::arg("direction"), py::arg("x_direction"))
        .def_property("location", &gp_Ax3::Location, &gp_Ax3::SetLocation, "Axis origin")
        .def_property("direction", &gp_Ax3::Direction, &gp_Ax3::SetDirection, "Main direction")
        .def_property("x_direction", &gp_Ax3::XDirection, &gp_Ax3::SetXDirection, "X direction")
        .def_property("y_direction", &gp_Ax3::YDirection, &gp_Ax3::SetYDirection, "Y direction")
        .def("ax2", &gp_Ax3::Ax2, "Return equivalent gp_Ax2")
        .def("__repr__", [](const gp_Ax3& axis) {
            const auto loc = axis.Location();
            const auto dir = axis.Direction();
            return "Ax3(location=(" + std::to_string(loc.X()) + ", " + std::to_string(loc.Y()) + ", " + std::to_string(loc.Z()) + ")"
                   ", direction=(" + std::to_string(dir.X()) + ", " + std::to_string(dir.Y()) + ", " + std::to_string(dir.Z()) + "))";
        });

    py::class_<gp_Circ>(m, "Circ")
        .def(py::init<>())
        .def(py::init<const gp_Ax2&, double>(), py::arg("axis"), py::arg("radius"))
        .def_property("position", &gp_Circ::Position, &gp_Circ::SetPosition, "Circle plane and orientation")
        .def_property("location", &gp_Circ::Location, &gp_Circ::SetLocation, "Circle center")
        .def_property("radius", &gp_Circ::Radius, &gp_Circ::SetRadius, "Circle radius")
        .def("axis", &gp_Circ::Axis, "Return circle axis as gp_Ax1")
        .def("__repr__", [](const gp_Circ& circ) {
            const auto loc = circ.Location();
            return "Circ(center=(" + std::to_string(loc.X()) + ", " + std::to_string(loc.Y()) + ", " + std::to_string(loc.Z())
                   + "), radius=" + std::to_string(circ.Radius()) + ")";
        });

    m.def(
        "distance",
        &Distance2d,
        py::arg("first"),
        py::arg("second"),
        "Compute the distance between two points"
    );

    std::cout << "[springocct] module init\n";

    m.def("compression_spring_solid", []() -> int {
        std::cout << "[springocct] compression_spring_solid binding called\n";

        int result = compression_spring_solid();

        std::cout << "[springocct] compression_spring_solid result = " << result << "\n";

        return result;
    });
}
