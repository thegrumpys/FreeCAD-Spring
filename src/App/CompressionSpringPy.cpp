#include "SpringConfig.h"

#include <Base/Console.h>
#include <Base/Interpreter.h>

#include <pybind11/pybind11.h>

namespace py = pybind11;

namespace Spring
{
void logTargetPlatform();
}

PYBIND11_MODULE(SpringCpp, m)
{
    m.doc() = "Bindings for the FreeCAD Spring workbench C++ helpers";
    m.def(
        "log_target_platform",
        []() {
            Spring::logTargetPlatform();
            return SPRING_TARGET_PLATFORM;
        },
        "Report the compiled platform string for diagnostics"
    );
}
