#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

mkdir -p "$ROOT_DIR/src/App"
mkdir -p "$ROOT_DIR/src/cmake"
mkdir -p "$ROOT_DIR/lib/Linux/SpringCpp"
mkdir -p "$ROOT_DIR/lib/Mac/SpringCpp"
mkdir -p "$ROOT_DIR/lib/Windows/SpringCpp"

if [ ! -f "$ROOT_DIR/src/CMakeLists.txt" ]; then
  cat <<'EOF' > "$ROOT_DIR/src/CMakeLists.txt"
cmake_minimum_required(VERSION 3.16)
project(SpringWorkbench LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

list(PREPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

if(NOT SPRING_TARGET_PLATFORM)
  set(SPRING_TARGET_PLATFORM "Generic")
endif()

find_package(FreeCAD MODULE REQUIRED COMPONENTS Base App)
find_package(pybind11 REQUIRED)

add_subdirectory(App)
EOF
fi


if [ ! -f "$ROOT_DIR/src/SpringConfig.h.in" ]; then
  cat <<'EOF' > "$ROOT_DIR/src/SpringConfig.h.in"
#pragma once

#define SPRING_VERSION "0.1.0"
#define SPRING_TARGET_PLATFORM "@SPRING_TARGET_PLATFORM@"
EOF
fi

if [ ! -f "$ROOT_DIR/src/App/CMakeLists.txt" ]; then
  cat <<'EOF' > "$ROOT_DIR/src/App/CMakeLists.txt"
set(SPRING_APP_TARGET SpringApp)

configure_file(
    ${CMAKE_SOURCE_DIR}/SpringConfig.h.in
    ${CMAKE_CURRENT_BINARY_DIR}/SpringConfig.h
    @ONLY
)

add_library(${SPRING_APP_TARGET} SHARED
    CompressionSpring.cpp
    CompressionSpringPy.cpp
)

target_include_directories(${SPRING_APP_TARGET}
    PRIVATE
        ${FREECAD_INCLUDE_DIR}
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${CMAKE_CURRENT_BINARY_DIR}
)

target_link_libraries(${SPRING_APP_TARGET}
    PRIVATE
        ${FreeCAD_Base_LIBS}
        ${FreeCAD_App_LIBS}
        pybind11::module
)

set(_output_dir "${CMAKE_BINARY_DIR}/lib/${SPRING_TARGET_PLATFORM}/SpringCpp")
set_target_properties(${SPRING_APP_TARGET} PROPERTIES
    OUTPUT_NAME SpringCpp
    LIBRARY_OUTPUT_DIRECTORY "${_output_dir}"
    RUNTIME_OUTPUT_DIRECTORY "${_output_dir}"
    ARCHIVE_OUTPUT_DIRECTORY "${_output_dir}"
)
EOF
fi

if [ ! -f "$ROOT_DIR/src/App/CompressionSpring.cpp" ]; then
  cat <<'EOF' > "$ROOT_DIR/src/App/CompressionSpring.cpp"
#include "SpringConfig.h"

#include <Base/Console.h>

namespace Spring
{
void logTargetPlatform()
{
    Base::Console().Log("Spring compression library built for %s
", SPRING_TARGET_PLATFORM);
}
} // namespace Spring
EOF
fi

if [ ! -f "$ROOT_DIR/src/App/CompressionSpringPy.cpp" ]; then
  cat <<'EOF' > "$ROOT_DIR/src/App/CompressionSpringPy.cpp"
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
EOF
fi

for platform in Linux Mac Windows; do
  init_path="$ROOT_DIR/lib/${platform}/SpringCpp/__init__.py"
  readme_path="$ROOT_DIR/lib/${platform}/SpringCpp/README.md"
  if [ ! -f "$init_path" ]; then
    cat <<EOF > "$init_path"
"""${platform} binary distribution of the SpringCpp module."""
EOF
  fi
  if [ ! -f "$readme_path" ]; then
    cat <<EOF > "$readme_path"
# SpringCpp ${platform} Payload

Place the compiled platform binary and any supporting libraries in this directory.
EOF
  fi
done

if [ ! -f "$ROOT_DIR/Makefile" ]; then
  python3 - <<'PYMK' "$ROOT_DIR/Makefile"
from pathlib import Path
import sys

Path(sys.argv[1]).write_text("""# Build helper for the FreeCAD Spring workbench hybrid Python/C++ module

BUILD_DIR ?= build
GENERATOR ?=
CMAKE ?= cmake
PYTHON ?= python3

# Additional flags to hand to CMake during configuration
CMAKE_ARGS ?=
EXTRA_CMAKE_ARGS ?=

PLATFORMS := linux macos windows

.PHONY: all clean $(addprefix configure-,$(PLATFORMS)) $(addprefix build-,$(PLATFORMS))

all: build-macos

define CONFIGURE_template
configure-$(1):
\t$(CMAKE) -S src -B $(BUILD_DIR)/$(1) $(GENERATOR) $(CMAKE_ARGS) $(EXTRA_CMAKE_ARGS) -DCMAKE_BUILD_TYPE=Release -DSPRING_TARGET_PLATFORM=$(1)

build-$(1): configure-$(1)
\t$(CMAKE) --build $(BUILD_DIR)/$(1) --config Release
endef

$(foreach plat,$(PLATFORMS),$(eval $(call CONFIGURE_template,$(plat))))

clean:
\trm -rf $(BUILD_DIR)
""")
PYMK
fi

echo "C++ layout scaffolding ensured."
