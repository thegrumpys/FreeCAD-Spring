# FreeCAD Spring Module

This repository hosts a simple Test workbench that exposes the OpenCascade `gp_Pnt2d` class to Python. The module is designed to be symlinked into FreeCAD's `src/Mod` directory as `Spring` and expects FreeCAD's `src/Mod/CMakeLists.txt` to contain `add_subdirectory(Spring)`.

## Layout

```
Spring/
├── App/
│   └── TestPnt2dModule.cpp    # Python extension that exposes gp_Pnt2d helpers
├── Init.py                    # Python API that imports the compiled module
├── InitGui.py                 # Minimal FreeCAD-style workbench definition
├── tests/
│   └── gp_Pnt2d_dump.cpp      # Standalone console test
└── CMakeLists.txt             # Builds the shared module and the console test
```

## Building

From the FreeCAD build tree, CMake will automatically discover the module once the symlink is in place. If you would like to build this repository independently you can run:

```
cmake -S Spring -B build
cmake --build build
```

This produces the `SpringTestWorkbench` Python module and the `test_gp_Pnt2d` console executable.

> **Note:** Some OpenCascade builds only expose the umbrella `OpenCASCADE::OpenCASCADE` target instead of individual
> libraries such as `OpenCASCADE::TKMath`. The CMake project now detects whichever target your toolchain provides, so
> FreeCAD's `pixi run configure` step no longer fails with the `Specified unsupported component: TKMath` error.

## Testing the gp_Pnt2d helper

1. Run the console test to verify the OpenCascade dependency is functioning:

   ```
   ./build/test_gp_Pnt2d
   ```

2. Launch Python, ensure `PYTHONPATH` includes the build folder, and run:

   ```python
   import Spring.Init as SpringInit
   print(SpringInit.describe_point(12.3, 45.6))
   ```

Both tests demonstrate that the module can construct `gp_Pnt2d` instances from C++ and surface the data back to Python.
