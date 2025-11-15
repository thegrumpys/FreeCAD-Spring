# Minimal FreeCAD discovery helper that works with both source checkouts and
# binary installations that omit FreeCADConfig.cmake.
#
# The upstream packages usually ship a FreeCADConfig.cmake file, but some
# distributions omit it. This module reconstructs the required include/lib
# directories from a combination of Python probes, freecadcmd output, and
# environment variables.

if(NOT Python3_EXECUTABLE)
  find_package(Python3 COMPONENTS Interpreter REQUIRED)
endif()

set(_spring_freecad_candidates)
set(_spring_freecad_err_python "")
set(_spring_freecad_err_console "")

function(_spring_add_freecad_candidate prefix include_dir lib_dir home_dir)
  if(prefix STREQUAL "")
    return()
  endif()

  if(IS_ABSOLUTE "${prefix}")
    set(_prefix "${prefix}")
  else()
    get_filename_component(_prefix "${prefix}" ABSOLUTE)
  endif()

  if(include_dir STREQUAL "")
    set(include_dir "${_prefix}/include")
  endif()
  if(lib_dir STREQUAL "")
    set(lib_dir "${_prefix}/lib")
  endif()
  if(home_dir STREQUAL "")
    set(home_dir "${_prefix}/Mod")
  endif()

  list(APPEND _spring_freecad_candidates "${_prefix}|${include_dir}|${lib_dir}|${home_dir}")
  list(REMOVE_DUPLICATES _spring_freecad_candidates)
  set(_spring_freecad_candidates "${_spring_freecad_candidates}" PARENT_SCOPE)
endfunction()

set(_spring_freecad_probe [=[
import pathlib, sys
try:
    import FreeCAD
except Exception as exc:
    sys.stderr.write('Failed to import FreeCAD: %s\n' % exc)
    sys.exit(1)
home = pathlib.Path(FreeCAD.getHomePath()).resolve()
prefix = home.parent
paths = [
    prefix,
    prefix / 'include',
    prefix / 'lib',
    prefix / 'lib' / 'cmake' / 'FreeCAD',
    prefix / 'share' / 'cmake' / 'FreeCAD',
]
print('\n'.join(str(p) for p in paths))
]=])

set(_spring_freecad_out "")
set(_spring_freecad_status -1)

execute_process(
  COMMAND "${Python3_EXECUTABLE}" -c "${_spring_freecad_probe}"
  OUTPUT_VARIABLE _spring_freecad_out
  ERROR_VARIABLE _spring_freecad_err_python
  RESULT_VARIABLE _spring_freecad_status
)

if(_spring_freecad_status EQUAL 0)
  string(REPLACE "\r" "" _spring_freecad_out "${_spring_freecad_out}")
  string(REGEX REPLACE "\n$" "" _spring_freecad_out "${_spring_freecad_out}")
  string(REPLACE "\n" ";" _spring_freecad_list "${_spring_freecad_out}")
  list(LENGTH _spring_freecad_list _spring_freecad_len)
  if(_spring_freecad_len GREATER 2)
    list(GET _spring_freecad_list 0 _probe_prefix)
    list(GET _spring_freecad_list 1 _probe_include)
    list(GET _spring_freecad_list 2 _probe_lib)
    _spring_add_freecad_candidate("${_probe_prefix}" "${_probe_include}" "${_probe_lib}" "")
    set(_probe_cfg_one "")
    set(_probe_cfg_two "")
    if(_spring_freecad_len GREATER 3)
      list(GET _spring_freecad_list 3 _probe_cfg_one)
    endif()
    if(_spring_freecad_len GREATER 4)
      list(GET _spring_freecad_list 4 _probe_cfg_two)
    endif()
    set(FreeCAD_CONFIG_DIRS)
    foreach(_cfg IN LISTS _probe_cfg_one _probe_cfg_two)
      if(EXISTS "${_cfg}")
        list(APPEND FreeCAD_CONFIG_DIRS "${_cfg}")
      endif()
    endforeach()
  endif()
endif()

if(NOT _spring_freecad_status EQUAL 0)
  find_program(_spring_freecad_console
    NAMES freecadcmd FreeCADCmd
    DOC "FreeCAD console executable used to query installation paths"
  )

  if(_spring_freecad_console)
    execute_process(
      COMMAND "${_spring_freecad_console}" -c "${_spring_freecad_probe}"
      OUTPUT_VARIABLE _spring_freecad_out
      ERROR_VARIABLE _spring_freecad_err_console
      RESULT_VARIABLE _spring_freecad_status
    )

    if(_spring_freecad_status EQUAL 0)
      string(REPLACE "\r" "" _spring_freecad_out "${_spring_freecad_out}")
      string(REGEX REPLACE "\n$" "" _spring_freecad_out "${_spring_freecad_out}")
      string(REPLACE "\n" ";" _spring_freecad_list "${_spring_freecad_out}")
      list(LENGTH _spring_freecad_list _spring_freecad_len)
      if(_spring_freecad_len GREATER 2)
        list(GET _spring_freecad_list 0 _probe_prefix)
        list(GET _spring_freecad_list 1 _probe_include)
        list(GET _spring_freecad_list 2 _probe_lib)
        _spring_add_freecad_candidate("${_probe_prefix}" "${_probe_include}" "${_probe_lib}" "")
      endif()
    endif()
  endif()
endif()

if(DEFINED ENV{FREECAD_PREFIX} AND NOT "$ENV{FREECAD_PREFIX}" STREQUAL "")
  _spring_add_freecad_candidate("$ENV{FREECAD_PREFIX}" "" "" "")
endif()

if(DEFINED ENV{FREECAD_HOME} AND NOT "$ENV{FREECAD_HOME}" STREQUAL "")
  get_filename_component(_freecad_home_prefix "$ENV{FREECAD_HOME}" DIRECTORY)
  _spring_add_freecad_candidate("${_freecad_home_prefix}" "" "" "$ENV{FREECAD_HOME}")
endif()

list(REMOVE_DUPLICATES _spring_freecad_candidates)

if(NOT _spring_freecad_candidates)
  set(_spring_freecad_msg "Failed to locate FreeCAD installation directories.")
  if(_spring_freecad_err_python)
    string(APPEND _spring_freecad_msg "\nPython error:\n${_spring_freecad_err_python}")
  endif()
  if(_spring_freecad_err_console)
    string(APPEND _spring_freecad_msg "\nfreecadcmd error:\n${_spring_freecad_err_console}")
  endif()
  if(FreeCAD_FIND_REQUIRED)
    message(FATAL_ERROR "${_spring_freecad_msg}")
  endif()
  set(FreeCAD_FOUND FALSE)
  return()
endif()

if(NOT FreeCAD_FIND_COMPONENTS)
  set(FreeCAD_FIND_COMPONENTS Base App)
endif()

set(_spring_freecad_success FALSE)
set(_spring_freecad_attempts)
set(_spring_freecad_missing_headers FALSE)

foreach(_candidate IN LISTS _spring_freecad_candidates)
  string(REPLACE "|" ";" _parts "${_candidate}")
  list(GET _parts 0 _prefix)
  list(GET _parts 1 _include_dir)
  list(GET _parts 2 _lib_dir)
  list(GET _parts 3 _home_dir)

  if(NOT EXISTS "${_prefix}")
    continue()
  endif()

  if(NOT EXISTS "${_include_dir}")
    set(_include_dir)
    foreach(_suffix "include" "Resources/include")
      set(_candidate "${_prefix}/${_suffix}")
      if(EXISTS "${_candidate}")
        set(_include_dir "${_candidate}")
        break()
      endif()
    endforeach()
  endif()
  if(NOT EXISTS "${_lib_dir}")
    set(_lib_dir)
    foreach(_suffix "lib" "Resources/lib")
      set(_candidate "${_prefix}/${_suffix}")
      if(EXISTS "${_candidate}")
        set(_lib_dir "${_candidate}")
        break()
      endif()
    endforeach()
  endif()
  if(NOT EXISTS "${_home_dir}")
    set(_home_dir "${_prefix}/Mod")
  endif()

  list(APPEND _spring_freecad_attempts "prefix=${_prefix}; include=${_include_dir}; lib=${_lib_dir}")

  set(_have_include TRUE)
  if(_include_dir STREQUAL "" OR NOT EXISTS "${_include_dir}")
    set(_have_include FALSE)
  endif()

  if(_include_dir STREQUAL "" OR _lib_dir STREQUAL "" OR
     NOT EXISTS "${_include_dir}" OR NOT EXISTS "${_lib_dir}")
    if(NOT _have_include AND EXISTS "${_lib_dir}")
      set(_spring_freecad_missing_headers TRUE)
    endif()
    continue()
  endif()

  set(_spring_freecad_lib_search
    "${_lib_dir}"
    "${_lib_dir}/FreeCAD"
    "${_lib_dir}/freecad"
  )

  unset(FreeCAD_Base_LIBRARY CACHE)
  unset(FreeCAD_App_LIBRARY CACHE)

  list(FIND FreeCAD_FIND_COMPONENTS "Base" _need_base)
  if(_need_base GREATER -1)
    find_library(FreeCAD_Base_LIBRARY
      NAMES FreeCADBase
      PATHS ${_spring_freecad_lib_search}
      NO_DEFAULT_PATH
    )
    set(FreeCAD_Base_FOUND FALSE)
    if(FreeCAD_Base_LIBRARY)
      set(FreeCAD_Base_FOUND TRUE)
      set(FreeCAD_Base_LIBS "${FreeCAD_Base_LIBRARY}")
    endif()
  endif()

  list(FIND FreeCAD_FIND_COMPONENTS "App" _need_app)
  if(_need_app GREATER -1)
    find_library(FreeCAD_App_LIBRARY
      NAMES FreeCADApp
      PATHS ${_spring_freecad_lib_search}
      NO_DEFAULT_PATH
    )
    set(FreeCAD_App_FOUND FALSE)
    if(FreeCAD_App_LIBRARY)
      set(FreeCAD_App_FOUND TRUE)
      set(FreeCAD_App_LIBS "${FreeCAD_App_LIBRARY}")
    endif()
  endif()

  set(_have_all TRUE)
  foreach(_component IN LISTS FreeCAD_FIND_COMPONENTS)
    if(NOT FreeCAD_${_component}_FOUND)
      set(_have_all FALSE)
      break()
    endif()
  endforeach()

  if(NOT _have_all)
    continue()
  endif()

  set(FREECAD_INCLUDE_DIR "${_include_dir}")
  set(FREECAD_LIB_DIR "${_lib_dir}")
  set(FREECAD_HOME_PATH "${_home_dir}")

  if(NOT DEFINED QT_HOST_PATH OR QT_HOST_PATH STREQUAL "")
    set(_spring_qt_host_candidate "${_prefix}/qt-host")
    if(EXISTS "${_spring_qt_host_candidate}")
      set(QT_HOST_PATH "${_spring_qt_host_candidate}" CACHE PATH
        "Host Qt installation paired with the detected FreeCAD SDK" FORCE)
    endif()
  endif()

  if(NOT DEFINED QT_HOST_PATH OR QT_HOST_PATH STREQUAL "")
    if(DEFINED ENV{CONDA_PREFIX} AND NOT "$ENV{CONDA_PREFIX}" STREQUAL "")
      set(_spring_qt_host_candidate "$ENV{CONDA_PREFIX}")
      if(EXISTS "${_spring_qt_host_candidate}/lib/cmake/Qt6Core"
          OR EXISTS "${_spring_qt_host_candidate}/bin/qtpaths"
          OR EXISTS "${_spring_qt_host_candidate}/bin/qtpaths6")
        set(QT_HOST_PATH "${_spring_qt_host_candidate}" CACHE PATH
          "Host Qt installation provided by the active pixi environment" FORCE)
      endif()
    endif()
  endif()

  set(_spring_freecad_interface_includes "${FREECAD_INCLUDE_DIR}")
  if(EXISTS "${FREECAD_INCLUDE_DIR}/FreeCAD")
    list(APPEND _spring_freecad_interface_includes "${FREECAD_INCLUDE_DIR}/FreeCAD")
  endif()
  list(REMOVE_DUPLICATES _spring_freecad_interface_includes)

  set(FREECAD_INCLUDE_DIRS "${_spring_freecad_interface_includes}")
  set(FREECAD_LIB_DIRS "${FREECAD_LIB_DIR}")

  set(FreeCAD_CONFIG_DIRS)
  foreach(_suffix "lib/cmake/FreeCAD" "share/cmake/FreeCAD" "cmake")
    set(_cfg_dir "${_prefix}/${_suffix}")
    if(EXISTS "${_cfg_dir}")
      list(APPEND FreeCAD_CONFIG_DIRS "${_cfg_dir}")
    endif()
  endforeach()
  list(REMOVE_DUPLICATES FreeCAD_CONFIG_DIRS)

  set(_spring_freecad_success TRUE)
  break()
endforeach()

if(NOT _spring_freecad_success)
  set(_spring_freecad_msg "Unable to locate FreeCAD libraries and headers.")
  if(_spring_freecad_attempts)
    string(APPEND _spring_freecad_msg "\nChecked candidates:\n  - ")
    string(REPLACE ";" "\n  - " _spring_attempt_lines "${_spring_freecad_attempts}")
    string(APPEND _spring_freecad_msg "${_spring_attempt_lines}")
  endif()
  if(_spring_freecad_err_python)
    string(APPEND _spring_freecad_msg "\nPython error:\n${_spring_freecad_err_python}")
  endif()
  if(_spring_freecad_err_console)
    string(APPEND _spring_freecad_msg "\nfreecadcmd error:\n${_spring_freecad_err_console}")
  endif()
  if(_spring_freecad_missing_headers)
    string(APPEND _spring_freecad_msg "\nThe detected FreeCAD installation exposes libraries but no headers. "
      "Packaged application bundles often omit developer headers; install FreeCAD via pixi or "
      "point CMake at a source build or SDK that includes them.")
  endif()
  if(FreeCAD_FIND_REQUIRED)
    message(FATAL_ERROR "${_spring_freecad_msg}")
  endif()
  set(FreeCAD_FOUND FALSE)
  return()
endif()

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(
  FreeCAD
  REQUIRED_VARS FREECAD_INCLUDE_DIR FREECAD_LIB_DIR
  HANDLE_COMPONENTS
)

if(NOT FreeCAD_FOUND)
  return()
endif()

set(FreeCAD_LIBRARIES)
if(FreeCAD_App_LIBRARY)
  list(APPEND FreeCAD_LIBRARIES "${FreeCAD_App_LIBRARY}")
endif()
if(FreeCAD_Base_LIBRARY)
  list(APPEND FreeCAD_LIBRARIES "${FreeCAD_Base_LIBRARY}")
endif()

if(FreeCAD_Base_LIBRARY AND NOT TARGET FreeCAD::Base)
  add_library(FreeCAD::Base UNKNOWN IMPORTED)
  set_target_properties(FreeCAD::Base PROPERTIES
    IMPORTED_LOCATION "${FreeCAD_Base_LIBRARY}"
    INTERFACE_INCLUDE_DIRECTORIES "${FREECAD_INCLUDE_DIRS}"
  )
endif()

if(FreeCAD_App_LIBRARY AND NOT TARGET FreeCAD::App)
  add_library(FreeCAD::App UNKNOWN IMPORTED)
  set_target_properties(FreeCAD::App PROPERTIES
    IMPORTED_LOCATION "${FreeCAD_App_LIBRARY}"
    INTERFACE_INCLUDE_DIRECTORIES "${FREECAD_INCLUDE_DIRS}"
  )
  if(TARGET FreeCAD::Base)
    set_property(TARGET FreeCAD::App PROPERTY INTERFACE_LINK_LIBRARIES FreeCAD::Base)
  endif()
endif()

mark_as_advanced(
  FreeCAD_Base_LIBRARY
  FreeCAD_App_LIBRARY
  FREECAD_INCLUDE_DIR
  FREECAD_LIB_DIR
)
