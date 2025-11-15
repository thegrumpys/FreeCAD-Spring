cmake_minimum_required(VERSION 3.16)
project(SpringWorkbench LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

list(PREPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

get_filename_component(SPRING_WORKBENCH_ROOT
    "${CMAKE_CURRENT_SOURCE_DIR}/.." ABSOLUTE)

set(SPRING_MOD_BUILD_DIR "${CMAKE_BINARY_DIR}/Mod/Spring")

set(_spring_python_files
    Init.py
    InitGui.py
    package.xml
)

set(_spring_python_directories
    Commands
    Dialogs
    Features
    Preferences
    Resources
    Spring
)

set(_spring_python_copy_outputs)

foreach(_spring_python_file IN LISTS _spring_python_files)
    get_filename_component(_spring_python_name "${_spring_python_file}" NAME)
    set(_spring_python_source
        "${SPRING_WORKBENCH_ROOT}/${_spring_python_file}")
    set(_spring_python_destination
        "${SPRING_MOD_BUILD_DIR}/${_spring_python_name}")

    add_custom_command(
        OUTPUT "${_spring_python_destination}"
        COMMAND ${CMAKE_COMMAND} -E make_directory "${SPRING_MOD_BUILD_DIR}"
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
                "${_spring_python_source}"
                "${_spring_python_destination}"
        DEPENDS "${_spring_python_source}"
        VERBATIM
        COMMENT "Copying ${_spring_python_name} to build Mod directory"
    )

    list(APPEND _spring_python_copy_outputs "${_spring_python_destination}")
endforeach()

foreach(_spring_python_dir IN LISTS _spring_python_directories)
    set(_spring_python_source_dir
        "${SPRING_WORKBENCH_ROOT}/${_spring_python_dir}")
    set(_spring_python_destination_dir
        "${SPRING_MOD_BUILD_DIR}/${_spring_python_dir}")
    set(_spring_python_stamp
        "${_spring_python_destination_dir}/.spring-sync")

    file(GLOB_RECURSE _spring_python_dir_contents CONFIGURE_DEPENDS
        "${_spring_python_source_dir}/*")

    add_custom_command(
        OUTPUT "${_spring_python_stamp}"
        COMMAND ${CMAKE_COMMAND} -E remove_directory
                "${_spring_python_destination_dir}"
        COMMAND ${CMAKE_COMMAND} -E copy_directory
                "${_spring_python_source_dir}"
                "${_spring_python_destination_dir}"
        COMMAND ${CMAKE_COMMAND} -E touch "${_spring_python_stamp}"
        DEPENDS ${_spring_python_dir_contents}
        VERBATIM
        COMMENT "Syncing ${_spring_python_dir} package into build tree"
    )

    list(APPEND _spring_python_copy_outputs "${_spring_python_stamp}")
endforeach()

if(_spring_python_copy_outputs)
    add_custom_target(SpringPython ALL
        DEPENDS ${_spring_python_copy_outputs})
endif()

set(_spring_python_install_sources)

foreach(_spring_python_file IN LISTS _spring_python_files)
    list(APPEND _spring_python_install_sources
        "${SPRING_WORKBENCH_ROOT}/${_spring_python_file}")
endforeach()

if(_spring_python_install_sources)
    install(FILES ${_spring_python_install_sources}
        DESTINATION "Mod/Spring")
endif()

foreach(_spring_python_dir IN LISTS _spring_python_directories)
    install(
        DIRECTORY "${SPRING_WORKBENCH_ROOT}/${_spring_python_dir}"
        DESTINATION "Mod/Spring"
        PATTERN "__pycache__" EXCLUDE
        PATTERN "*.pyc" EXCLUDE
    )
endforeach()

if(NOT SPRING_TARGET_PLATFORM)
  set(SPRING_TARGET_PLATFORM "Generic")
endif()

# When the Spring workbench is built as part of a complete FreeCAD tree the
# FreeCAD targets are already available. Fall back to locating an installed or
# standalone FreeCAD build only when they are missing so the project can still
# be configured independently for development or testing.
if(
    NOT TARGET FreeCAD::App
    AND NOT TARGET FreeCADApp
    AND NOT TARGET FreeCAD::Base
    AND NOT TARGET FreeCADBase
)
  set(_spring_default_freecad_source_dir "")
  if(DEFINED ENV{FREECAD_SOURCE_DIR} AND NOT "$ENV{FREECAD_SOURCE_DIR}" STREQUAL "")
    set(_spring_default_freecad_source_dir "$ENV{FREECAD_SOURCE_DIR}")
  elseif(DEFINED ENV{HOME})
    set(_spring_home_candidate "$ENV{HOME}/git/FreeCAD")
    if(EXISTS "${_spring_home_candidate}")
      set(_spring_default_freecad_source_dir "${_spring_home_candidate}")
    endif()
  endif()

  set(FREECAD_SOURCE_DIR "${_spring_default_freecad_source_dir}" CACHE PATH
      "Path to the FreeCAD source tree that provides headers under src/.")

  find_package(FreeCAD MODULE REQUIRED COMPONENTS Base App)
endif()

find_package(pybind11 REQUIRED)

add_subdirectory(App)
