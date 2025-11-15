cmake_minimum_required(VERSION 3.16)

# The Spring workbench can be added directly to FreeCAD's src/Mod tree or built
# independently for development. Delegate the heavy lifting to the existing
# CMake logic under src/ which supports both workflows.
add_subdirectory(src)
