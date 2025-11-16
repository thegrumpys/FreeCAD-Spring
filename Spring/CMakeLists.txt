cmake_minimum_required(VERSION 3.16)
project(SpringTestWorkbench LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

find_package(Python3 COMPONENTS Development REQUIRED)
find_package(OpenCASCADE REQUIRED)

if (TARGET OpenCASCADE::TKMath)
    set(Spring_OCC_MATH_TARGET OpenCASCADE::TKMath)
elseif (TARGET OpenCASCADE::OpenCASCADE)
    set(Spring_OCC_MATH_TARGET OpenCASCADE::OpenCASCADE)
else()
    message(FATAL_ERROR "OpenCASCADE package missing TKMath and umbrella target. Cannot link Spring workbench.")
endif()

add_library(SpringTestWorkbench MODULE
    App/TestPnt2dModule.cpp
)

target_include_directories(SpringTestWorkbench
    PRIVATE
        ${Python3_INCLUDE_DIRS}
)

target_link_libraries(SpringTestWorkbench
    PRIVATE
        Python3::Python
        ${Spring_OCC_MATH_TARGET}
)

set_target_properties(SpringTestWorkbench PROPERTIES
    PREFIX ""
)

add_executable(test_gp_Pnt2d
    tests/gp_Pnt2d_dump.cpp
)

target_link_libraries(test_gp_Pnt2d
    PRIVATE
        ${Spring_OCC_MATH_TARGET}
)
