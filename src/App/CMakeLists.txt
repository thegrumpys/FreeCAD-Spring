set(SPRING_APP_TARGET SpringApp)

configure_file(
    ${PROJECT_SOURCE_DIR}/SpringConfig.h.in
    ${CMAKE_CURRENT_BINARY_DIR}/SpringConfig.h
    @ONLY
)

add_library(${SPRING_APP_TARGET} SHARED
    CompressionSpring.cpp
    CompressionSpringPy.cpp
)

# FreeCAD's headers rely on C++20 features such as concepts and
# std::source_location, so make sure the Spring library is compiled with a
# matching language standard regardless of the user's global configuration.
target_compile_features(${SPRING_APP_TARGET} PRIVATE cxx_std_20)

set(_spring_private_includes
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_BINARY_DIR}
)
set(_spring_freecad_includes)
set(_spring_pycxx_extra)

if(NOT TARGET FreeCAD::App AND NOT TARGET FreeCADApp)
    set(_spring_freecad_includes ${FREECAD_INCLUDE_DIR})
    if(EXISTS "${FREECAD_INCLUDE_DIR}/FreeCAD")
        list(APPEND _spring_freecad_includes "${FREECAD_INCLUDE_DIR}/FreeCAD")
    endif()

    set(_spring_source_dir_raw)
    if(FREECAD_SOURCE_DIR)
        list(APPEND _spring_source_dir_raw "${FREECAD_SOURCE_DIR}")
    endif()
    if(DEFINED ENV{FREECAD_SOURCE_DIR} AND NOT "$ENV{FREECAD_SOURCE_DIR}" STREQUAL "")
        list(APPEND _spring_source_dir_raw "$ENV{FREECAD_SOURCE_DIR}")
    endif()

    set(_spring_source_dir_hints)
    foreach(_spring_source_entry IN LISTS _spring_source_dir_raw)
        if(NOT _spring_source_entry)
            continue()
        endif()
        string(REPLACE ":" ";" _spring_source_expanded "${_spring_source_entry}")
        foreach(_spring_source IN LISTS _spring_source_expanded)
            if(_spring_source)
                list(APPEND _spring_source_dir_hints "${_spring_source}")
            endif()
        endforeach()
    endforeach()

    list(REMOVE_DUPLICATES _spring_source_dir_hints)

    foreach(_spring_source_dir IN LISTS _spring_source_dir_hints)
        get_filename_component(_spring_source_dir_abs "${_spring_source_dir}" ABSOLUTE)
        set(_spring_source_candidate "${_spring_source_dir_abs}/src")
        if(
            EXISTS "${_spring_source_candidate}/Base/Console.h"
            OR EXISTS "${_spring_source_candidate}/QtCore.h"
        )
            list(APPEND _spring_freecad_includes "${_spring_source_candidate}")
        endif()

        set(_spring_source_pycxx "${_spring_source_dir_abs}/src/3rdParty/PyCXX")
        if(EXISTS "${_spring_source_pycxx}/CXX/Extensions.hxx")
            list(APPEND _spring_pycxx_extra "${_spring_source_pycxx}")
        endif()
    endforeach()

    set(_spring_build_dir_raw)
    if(FREECAD_BUILD_DIR)
        list(APPEND _spring_build_dir_raw "${FREECAD_BUILD_DIR}")
    endif()
    if(DEFINED ENV{FREECAD_BUILD_DIR} AND NOT "$ENV{FREECAD_BUILD_DIR}" STREQUAL "")
        list(APPEND _spring_build_dir_raw "$ENV{FREECAD_BUILD_DIR}")
    endif()

    set(_spring_build_dir_hints)
    foreach(_spring_hint_entry IN LISTS _spring_build_dir_raw)
        if(NOT _spring_hint_entry)
            continue()
        endif()
        string(REPLACE ":" ";" _spring_hint_expanded "${_spring_hint_entry}")
        foreach(_spring_hint IN LISTS _spring_hint_expanded)
            if(_spring_hint)
                list(APPEND _spring_build_dir_hints "${_spring_hint}")
            endif()
        endforeach()
    endforeach()

    list(REMOVE_DUPLICATES _spring_build_dir_hints)

    foreach(_spring_build_dir IN LISTS _spring_build_dir_hints)
        get_filename_component(_spring_build_dir_abs "${_spring_build_dir}" ABSOLUTE)
        set(_spring_build_candidate "${_spring_build_dir_abs}/src")
        if(
            EXISTS "${_spring_build_candidate}/Base/Console.h"
            OR EXISTS "${_spring_build_candidate}/QtCore.h"
        )
            list(APPEND _spring_freecad_includes "${_spring_build_candidate}")
        endif()

        set(_spring_build_pycxx "${_spring_build_dir_abs}/src/3rdParty/PyCXX")
        if(EXISTS "${_spring_build_pycxx}/CXX/Extensions.hxx")
            list(APPEND _spring_pycxx_extra "${_spring_build_pycxx}")
        endif()
    endforeach()

    list(REMOVE_DUPLICATES _spring_freecad_includes)
    list(APPEND _spring_private_includes ${_spring_freecad_includes})
endif()

set(_spring_pycxx_hints ${_spring_freecad_includes} ${_spring_pycxx_extra})

if(FREECAD_SOURCE_DIR)
    list(APPEND _spring_pycxx_hints "${FREECAD_SOURCE_DIR}/src/3rdParty/PyCXX")
endif()

if(FREECAD_BUILD_DIR)
    list(APPEND _spring_pycxx_hints "${FREECAD_BUILD_DIR}/src/3rdParty/PyCXX")
endif()

if(DEFINED ENV{FREECAD_SOURCE_DIR} AND NOT "$ENV{FREECAD_SOURCE_DIR}" STREQUAL "")
    list(APPEND _spring_pycxx_hints "$ENV{FREECAD_SOURCE_DIR}/src/3rdParty/PyCXX")
endif()

if(DEFINED ENV{FREECAD_BUILD_DIR} AND NOT "$ENV{FREECAD_BUILD_DIR}" STREQUAL "")
    list(APPEND _spring_pycxx_hints "$ENV{FREECAD_BUILD_DIR}/src/3rdParty/PyCXX")
endif()

if(NOT CMAKE_SOURCE_DIR STREQUAL PROJECT_SOURCE_DIR)
    list(APPEND _spring_pycxx_hints
        "${CMAKE_SOURCE_DIR}/src/3rdParty/PyCXX"
        "${CMAKE_BINARY_DIR}/src/3rdParty/PyCXX"
    )
endif()

if(FREECAD_INCLUDE_DIR AND EXISTS "${FREECAD_INCLUDE_DIR}")
    file(GLOB _spring_pycxx_site_packages
        LIST_DIRECTORIES TRUE
        "${FREECAD_INCLUDE_DIR}/python*/site-packages"
    )
    foreach(_spring_candidate IN LISTS _spring_pycxx_site_packages)
        if(EXISTS "${_spring_candidate}/CXX/Extensions.hxx")
            list(APPEND _spring_pycxx_hints "${_spring_candidate}")
        endif()
    endforeach()
endif()

if(FREECAD_PYCXX_INCLUDE_DIR)
    list(APPEND _spring_pycxx_hints "${FREECAD_PYCXX_INCLUDE_DIR}")
endif()

if(DEFINED ENV{FREECAD_PYCXX_INCLUDE_DIR} AND NOT "$ENV{FREECAD_PYCXX_INCLUDE_DIR}" STREQUAL "")
    list(APPEND _spring_pycxx_hints "$ENV{FREECAD_PYCXX_INCLUDE_DIR}")
endif()

if(Python3_INCLUDE_DIRS)
    list(APPEND _spring_pycxx_hints ${Python3_INCLUDE_DIRS})
endif()

list(REMOVE_DUPLICATES _spring_pycxx_hints)

unset(_spring_pycxx_header CACHE)
unset(_spring_pycxx_header)
find_path(
    _spring_pycxx_header
    CXX/Extensions.hxx
    PATHS ${_spring_pycxx_hints}
    NO_DEFAULT_PATH
)

if(NOT _spring_pycxx_header)
    find_path(
        _spring_pycxx_header
        Extensions.hxx
        PATH_SUFFIXES CXX
    )
endif()

if(_spring_pycxx_header)
    list(APPEND _spring_private_includes "${_spring_pycxx_header}")
else()
    message(FATAL_ERROR
        "CXX/Extensions.hxx was not found. Set FREECAD_PYCXX_INCLUDE_DIR to the "
        "directory that contains the PyCXX headers (often FreeCAD's include/"
        "pythonX.Y/site-packages) or ensure your FreeCAD installation ships "
        "them."
    )
endif()

target_include_directories(${SPRING_APP_TARGET}
    PRIVATE
        ${_spring_private_includes}
)

set(_spring_link_libs pybind11::module)
set(_spring_python_compile)
set(_spring_python_link)

foreach(_spring_python_candidate IN ITEMS Python3::Module Python::Module)
    if(TARGET ${_spring_python_candidate})
        set(_spring_python_compile ${_spring_python_candidate})
        break()
    endif()
endforeach()

foreach(_spring_python_candidate IN ITEMS Python3::Python Python::Python)
    if(TARGET ${_spring_python_candidate})
        set(_spring_python_link ${_spring_python_candidate})
        break()
    endif()
endforeach()

if(NOT _spring_python_compile OR NOT _spring_python_link)
    find_package(Python3 COMPONENTS Development.Module Development QUIET)

    if(NOT _spring_python_compile)
        foreach(_spring_python_candidate IN ITEMS Python3::Module)
            if(TARGET ${_spring_python_candidate})
                set(_spring_python_compile ${_spring_python_candidate})
                break()
            endif()
        endforeach()
    endif()

    if(NOT _spring_python_link)
        foreach(_spring_python_candidate IN ITEMS Python3::Python)
            if(TARGET ${_spring_python_candidate})
                set(_spring_python_link ${_spring_python_candidate})
                break()
            endif()
        endforeach()
    endif()
endif()

if(_spring_python_compile)
    list(APPEND _spring_link_libs ${_spring_python_compile})
endif()

if(_spring_python_link)
    list(APPEND _spring_link_libs ${_spring_python_link})
elseif(Python3_FOUND AND Python3_LIBRARIES)
    list(APPEND _spring_link_libs ${Python3_LIBRARIES})
elseif(DEFINED PYTHON_LIBRARIES AND PYTHON_LIBRARIES)
    list(APPEND _spring_link_libs ${PYTHON_LIBRARIES})
endif()
if(TARGET FreeCAD::App)
    list(APPEND _spring_link_libs FreeCAD::App)
elseif(TARGET FreeCADApp)
    list(APPEND _spring_link_libs FreeCADApp)
elseif(TARGET FreeCAD::Base)
    list(APPEND _spring_link_libs FreeCAD::Base ${FreeCAD_App_LIBS})
elseif(TARGET FreeCADBase)
    list(APPEND _spring_link_libs FreeCADBase ${FreeCAD_App_LIBS})
else()
    list(APPEND _spring_link_libs ${FreeCAD_Base_LIBS} ${FreeCAD_App_LIBS})
endif()

if(NOT TARGET fmt::fmt AND NOT TARGET fmt::fmt-header-only)
    find_package(fmt QUIET)
endif()

if(TARGET fmt::fmt)
    list(APPEND _spring_link_libs fmt::fmt)
elseif(TARGET fmt::fmt-header-only)
    target_compile_definitions(${SPRING_APP_TARGET} PRIVATE FMT_HEADER_ONLY=1)
elseif(DEFINED fmt_LIBRARIES AND fmt_LIBRARIES)
    list(APPEND _spring_link_libs ${fmt_LIBRARIES})
elseif(DEFINED FMT_LIBRARIES AND FMT_LIBRARIES)
    list(APPEND _spring_link_libs ${FMT_LIBRARIES})
endif()

find_package(Qt6 COMPONENTS Core QUIET)
if(Qt6_FOUND)
    list(APPEND _spring_link_libs Qt6::Core)
    find_package(Qt6Core5Compat QUIET)
    if(TARGET Qt6::Core5Compat)
        list(APPEND _spring_link_libs Qt6::Core5Compat)
    endif()
else()
    find_package(Qt5 COMPONENTS Core QUIET)
    if(Qt5_FOUND)
        list(APPEND _spring_link_libs Qt5::Core)
    else()
        message(FATAL_ERROR
            "Qt Core development files were not found. Install the Qt development headers (for example via `brew install qt@5` or your system package manager) before building Spring against a FreeCAD source checkout.")
    endif()
endif()

target_link_libraries(${SPRING_APP_TARGET}
    PRIVATE
        ${_spring_link_libs}
)

if(CMAKE_SOURCE_DIR STREQUAL PROJECT_SOURCE_DIR)
    set(_spring_default_output "${CMAKE_BINARY_DIR}/lib/${SPRING_TARGET_PLATFORM}/SpringCpp")
else()
    set(_spring_default_output "${CMAKE_BINARY_DIR}/Mod/Spring/lib/${SPRING_TARGET_PLATFORM}/SpringCpp")
endif()

set(SPRING_CPP_OUTPUT_DIR "${_spring_default_output}" CACHE PATH
    "Output directory for the compiled SpringCpp extension module")

file(MAKE_DIRECTORY "${SPRING_CPP_OUTPUT_DIR}")

get_filename_component(_spring_repo_root "${PROJECT_SOURCE_DIR}/.." ABSOLUTE)
set(_spring_pointer_dir "${_spring_repo_root}/lib/${SPRING_TARGET_PLATFORM}")
file(MAKE_DIRECTORY "${_spring_pointer_dir}")
get_filename_component(_spring_python_parent "${SPRING_CPP_OUTPUT_DIR}/.." ABSOLUTE)
set(_spring_pointer_file "${_spring_pointer_dir}/.springcpp-path")
file(WRITE "${_spring_pointer_file}" "${_spring_python_parent}\n")

set(_spring_build_rpath)
set(_spring_install_rpath)

if(NOT WIN32)
    if(APPLE)
        set(_spring_origin_token "@loader_path")
    else()
        set(_spring_origin_token "$ORIGIN")
    endif()

    set(_spring_relative_lib "${_spring_origin_token}/../../../../../lib")
    list(APPEND _spring_install_rpath "${_spring_relative_lib}")
    list(APPEND _spring_build_rpath "${_spring_relative_lib}")

    set(_spring_absolute_rpath_candidates)

    if(FREECAD_LIB_DIR)
        list(APPEND _spring_absolute_rpath_candidates "${FREECAD_LIB_DIR}")
    endif()

    if(FREECAD_LIB_DIRS)
        list(APPEND _spring_absolute_rpath_candidates ${FREECAD_LIB_DIRS})
    endif()

    if(DEFINED ENV{FREECAD_LIB_DIR} AND NOT "$ENV{FREECAD_LIB_DIR}" STREQUAL "")
        string(REPLACE ":" ";" _spring_env_lib "$ENV{FREECAD_LIB_DIR}")
        list(APPEND _spring_absolute_rpath_candidates ${_spring_env_lib})
    endif()

    set(_spring_build_dir_candidates)
    if(FREECAD_BUILD_DIR)
        list(APPEND _spring_build_dir_candidates "${FREECAD_BUILD_DIR}")
    endif()

    if(DEFINED ENV{FREECAD_BUILD_DIR} AND NOT "$ENV{FREECAD_BUILD_DIR}" STREQUAL "")
        string(REPLACE ":" ";" _spring_env_build "$ENV{FREECAD_BUILD_DIR}")
        list(APPEND _spring_build_dir_candidates ${_spring_env_build})
    endif()

    foreach(_spring_lib_hint IN LISTS _spring_build_dir_candidates)
        if(_spring_lib_hint)
            list(APPEND _spring_absolute_rpath_candidates
                "${_spring_lib_hint}/lib"
                "${_spring_lib_hint}/lib64"
            )
        endif()
    endforeach()

    foreach(_spring_rpath IN LISTS _spring_absolute_rpath_candidates)
        if(NOT _spring_rpath)
            continue()
        endif()

        get_filename_component(_spring_rpath_abs "${_spring_rpath}" ABSOLUTE)
        if(IS_ABSOLUTE "${_spring_rpath_abs}")
            list(APPEND _spring_build_rpath "${_spring_rpath_abs}")
        endif()
    endforeach()
endif()

if(_spring_build_rpath)
    list(REMOVE_DUPLICATES _spring_build_rpath)
endif()

if(_spring_install_rpath)
    list(REMOVE_DUPLICATES _spring_install_rpath)
endif()

set_target_properties(${SPRING_APP_TARGET} PROPERTIES
    OUTPUT_NAME SpringCpp
    LIBRARY_OUTPUT_DIRECTORY "${SPRING_CPP_OUTPUT_DIR}"
    RUNTIME_OUTPUT_DIRECTORY "${SPRING_CPP_OUTPUT_DIR}"
    ARCHIVE_OUTPUT_DIRECTORY "${SPRING_CPP_OUTPUT_DIR}"
    BUILD_RPATH "${_spring_build_rpath}"
    INSTALL_RPATH "${_spring_install_rpath}"
)

install(TARGETS ${SPRING_APP_TARGET}
    LIBRARY DESTINATION "Mod/Spring/lib/${SPRING_TARGET_PLATFORM}/SpringCpp"
    RUNTIME DESTINATION "Mod/Spring/lib/${SPRING_TARGET_PLATFORM}/SpringCpp"
    ARCHIVE DESTINATION "Mod/Spring/lib/${SPRING_TARGET_PLATFORM}/SpringCpp"
)
