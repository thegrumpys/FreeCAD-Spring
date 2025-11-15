# FreeCAD-Spring
Springs WorkBench for FreeCAD

## Building with pixi

This repository mirrors the build integration pattern used by FreeCAD itself, so
you can drive configuration, compilation, and installation through the `pixi`
tasks that ship with the upstream project.

Run the commands below from the FreeCAD source tree after the Spring workbench
has been linked into `src/Mod`:

1. Configure the build directory so CMake discovers the Spring module:
   ```bash
   pixi run configure
   ```
2. Compile the configured tree (this invokes the generator selected during the
   configure step, which defaults to Ninja on FreeCAD; you do not have to call
   `ninja` yourself):
   ```bash
   pixi run build
   ```
3. Optionally install the resulting binaries, modules, and resources:
   ```bash
   pixi run install
   ```

Always run the commands in the order shown above so each stage has the inputs it
expects.
