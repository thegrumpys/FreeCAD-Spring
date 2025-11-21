cmake_minimum_required(VERSION 3.16)

# The Spring workbench can be added directly to FreeCAD's src/Mod tree or built
# independently for development. Delegate the heavy lifting to the existing
# CMake logic under src/ which supports both workflows.
add_subdirectory(libspringocct)

# When the workbench is integrated into FreeCAD's build tree the Python entry
# points must be visible from the binary Mod/ directory. FreeCAD will look for
# ``Init.py``/``InitGui.py`` under ``<build>/Mod/Spring``; keep those files
# synchronized so developers do not see missing-module errors when launching a
# debug build.
set(SPRING_MOD_DESTINATION "${CMAKE_BINARY_DIR}/Mod/Spring")

set(SPRING_PYTHON_FILES
    Init.py
    InitGui.py
    README.md
    LICENSE
)

set(SPRING_PYTHON_DIRECTORIES
    Commands
    Dialogs
    Features
    Preferences
    Resources
    Spring
    Tests
)

add_custom_target(SpringWorkbenchPython ALL
    COMMAND ${CMAKE_COMMAND} -E make_directory "${SPRING_MOD_DESTINATION}"
)

foreach(py_file IN LISTS SPRING_PYTHON_FILES)
    add_custom_command(TARGET SpringWorkbenchPython POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different
            "${CMAKE_CURRENT_SOURCE_DIR}/${py_file}"
            "${SPRING_MOD_DESTINATION}/${py_file}"
    )
endforeach()

foreach(py_dir IN LISTS SPRING_PYTHON_DIRECTORIES)
    add_custom_command(TARGET SpringWorkbenchPython POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_directory
            "${CMAKE_CURRENT_SOURCE_DIR}/${py_dir}"
            "${SPRING_MOD_DESTINATION}/${py_dir}"
    )
endforeach()
